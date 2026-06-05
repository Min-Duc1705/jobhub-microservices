using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using CommonService.Events;
using CommonService.Storage;
using MassTransit;
using JobService.Models;
using JobService.Models.Enums;
using JobService.Models.Request;
using JobService.Models.Response;
using JobService.Repositories.Interface;
using JobService.Services.Interface;
using JobService.Specifications;
using Microsoft.Extensions.Options;

namespace JobService.Services;

public class JobServiceImpl : IJobService
{
    private readonly IJobRepository   _jobRepo;
    private readonly ISkillRepository _skillRepo;
    private readonly IMapper          _mapper;
    private readonly IPublishEndpoint _publishEndpoint;
    private readonly MinioSettings      _minioSettings;

    public JobServiceImpl(
        IJobRepository jobRepo, 
        ISkillRepository skillRepo, 
        IMapper mapper,
        IPublishEndpoint publishEndpoint,
        IOptions<MinioSettings> minioSettings)
    {
        _jobRepo         = jobRepo;
        _skillRepo       = skillRepo;
        _mapper          = mapper;
        _publishEndpoint = publishEndpoint;
        _minioSettings   = minioSettings.Value;
    }

    private JobResponse FormatUrls(JobResponse response)
    {
        if (response == null) return null!;
        response.CompanyLogo = MinioUrlHelper.ToAbsoluteUrl(response.CompanyLogo, _minioSettings, "companies");
        return response;
    }

    private List<JobResponse> FormatUrls(List<JobResponse> responses)
    {
        if (responses == null) return null!;
        foreach (var r in responses)
        {
            FormatUrls(r);
        }
        return responses;
    }

    public async Task<ResultPaginationDto<JobResponse>> GetAllAsync(JobFilterRequest filter)
    {
        var spec = new JobFilterSpec(
            filter.SearchTerm, filter.CompanyId, filter.CustomerId, filter.Location,
            filter.Level, filter.JobType, filter.Status,
            filter.SalaryMin, filter.SalaryMax, filter.SkillIds,
            filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);

        var countSpec = new JobFilterCountSpec(
            filter.SearchTerm, filter.CompanyId, filter.CustomerId, filter.Location,
            filter.Level, filter.JobType, filter.Status,
            filter.SalaryMin, filter.SalaryMax, filter.SkillIds);

        var items = await _jobRepo.ListAsync(spec);
        var total = await _jobRepo.CountAsync(countSpec);

        return new ResultPaginationDto<JobResponse>(
            FormatUrls(_mapper.Map<List<JobResponse>>(items)),
            filter.PageNumber, filter.PageSize, total);
    }

    public async Task<ResultPaginationDto<JobResponse>> GetAllForAdminAsync(AdminJobFilterRequest filter)
    {
        var spec = new AdminJobFilterSpec(
            filter.SearchTerm, filter.CompanyId, filter.CustomerId, filter.Location,
            filter.Level, filter.JobType, filter.Status,
            filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);

        var countSpec = new AdminJobCountSpec(
            filter.SearchTerm, filter.CompanyId, filter.CustomerId, filter.Location,
            filter.Level, filter.JobType, filter.Status);

        var items = await _jobRepo.ListAsync(spec);
        var total = await _jobRepo.CountAsync(countSpec);

        return new ResultPaginationDto<JobResponse>(
            FormatUrls(_mapper.Map<List<JobResponse>>(items)),
            filter.PageNumber, filter.PageSize, total);
    }

    public async Task<JobResponse> GetByIdAsync(Guid id, bool incrementView = true)
    {
        var spec = new JobByIdSpec(id);
        var job  = await _jobRepo.GetEntityWithSpec(spec);

        if (job == null)
            throw new NotFoundException($"Không tìm thấy tin tuyển dụng với ID: {id}");

        if (incrementView)
            await _jobRepo.IncrementViewCountAsync(id);

        return FormatUrls(_mapper.Map<JobResponse>(job));
    }

    public async Task<List<JobCategoryStatResponse>> GetJobCategoryStatsAsync()
    {
        var jobs = await _jobRepo.GetAllAsync();
        
        var publishedJobs = jobs.Where(j => j.Status == JobStatus.PUBLISHED).ToList();
        
        int total = publishedJobs.Count;
        if (total == 0)
        {
            return new List<JobCategoryStatResponse>();
        }

        var result = publishedJobs
            .GroupBy(j => string.IsNullOrWhiteSpace(j.Category) ? "Khác" : j.Category.Trim())
            .Select(g => new JobCategoryStatResponse
            {
                Name = g.Key,
                Count = g.Count(),
                Percentage = Math.Round((double)g.Count() / total * 100, 1)
            })
            .OrderByDescending(r => r.Count)
            .ToList();

        return result;
    }

    public async Task<JobResponse> CreateAsync(Guid customerId, CreateJobRequest request)
    {
        var job = _mapper.Map<Job>(request);
        job.CustomerId = customerId;
        job.Status     = JobStatus.DRAFT; // Mặc định là bản nháp

        if (job.StartDate == null)
        {
            job.StartDate = DateTime.UtcNow;
        }

        // Validate và gán kỹ năng
        if (request.SkillIds.Any())
        {
            var distinctIds = request.SkillIds.Distinct().ToList();
            var skills = await _skillRepo.GetByIdsAsync(distinctIds);
            if (skills.Count != distinctIds.Count)
                throw new BadRequestException("Một hoặc nhiều SkillId không hợp lệ.");

            job.JobSkills = skills.Select(s => new JobSkill
            {
                JobId   = job.Id,
                SkillId = s.Id
            }).ToList();
        }

        await _jobRepo.AddAsync(job);
        await _jobRepo.SaveChangesAsync();

        await PublishJobPublishedEventAsync(job.Id);

        return await GetByIdAsync(job.Id, incrementView: false);
    }

    public async Task<JobResponse> UpdateAsync(Guid id, UpdateJobRequest request)
    {
        var job = await _jobRepo.GetJobWithSkillsTrackedAsync(id);

        if (job == null)
            throw new NotFoundException($"Không tìm thấy tin tuyển dụng với ID: {id}");

        _mapper.Map(request, job);

        // Cập nhật skills nếu có truyền vào
        if (request.SkillIds != null)
        {
            var distinctIds = request.SkillIds.Distinct().ToList();
            var skills = await _skillRepo.GetByIdsAsync(distinctIds);
            if (skills.Count != distinctIds.Count)
                throw new BadRequestException("Một hoặc nhiều SkillId không hợp lệ.");

            // Xóa các kỹ năng cũ không còn được chọn
            var toRemove = job.JobSkills
                .Where(js => !distinctIds.Contains(js.SkillId))
                .ToList();
            foreach (var js in toRemove)
            {
                job.JobSkills.Remove(js);
            }

            // Thêm các kỹ năng mới chưa tồn tại trong danh sách của job
            var existingSkillIds = job.JobSkills.Select(js => js.SkillId).ToHashSet();
            foreach (var skillId in distinctIds)
            {
                if (!existingSkillIds.Contains(skillId))
                {
                    job.JobSkills.Add(new JobSkill
                    {
                        JobId   = job.Id,
                        SkillId = skillId
                    });
                }
            }
        }

        _jobRepo.Update(job);
        await _jobRepo.SaveChangesAsync();

        await PublishJobPublishedEventAsync(id);

        return await GetByIdAsync(id, incrementView: false);
    }

    public async Task DeleteAsync(Guid id)
    {
        var job = await _jobRepo.GetByIdAsync(id);
        if (job == null || job.IsDeleted)
            throw new NotFoundException($"Không tìm thấy tin tuyển dụng với ID: {id}");

        _jobRepo.Delete(job);
        await _jobRepo.SaveChangesAsync();
    }

    public async Task<JobResponse> ChangeStatusAsync(Guid id, string status)
    {
        var job = await _jobRepo.GetByIdAsync(id);
        if (job == null || job.IsDeleted)
            throw new NotFoundException($"Không tìm thấy tin tuyển dụng với ID: {id}");

        if (!Enum.TryParse<JobStatus>(status, ignoreCase: true, out var newStatus))
            throw new BadRequestException($"Trạng thái '{status}' không hợp lệ.");

        job.Status = newStatus;
        _jobRepo.Update(job);
        await _jobRepo.SaveChangesAsync();

        await PublishJobPublishedEventAsync(id);

        return FormatUrls(_mapper.Map<JobResponse>(job));
    }

    private int ParseYearsOfExperience(string? exp)
    {
        if (string.IsNullOrWhiteSpace(exp)) return 0;
        var match = System.Text.RegularExpressions.Regex.Match(exp, @"\d+");
        if (match.Success && int.TryParse(match.Value, out var years))
        {
            return years;
        }
        return 0;
    }

    private async Task PublishJobPublishedEventAsync(Guid jobId)
    {
        try
        {
            var spec = new JobByIdSpec(jobId);
            var job = await _jobRepo.GetEntityWithSpec(spec);
            if (job != null && job.Status == JobStatus.PUBLISHED)
            {
                var evt = new JobPublishedEvent
                {
                    JobId = job.Id,
                    JobTitle = job.Name,
                    YearsOfExperience = ParseYearsOfExperience(job.ExperienceRequired),
                    SkillSet = job.JobSkills
                        .Where(js => js.Skill != null)
                        .Select(js => js.Skill.Name)
                        .ToList(),
                    Location = job.Location ?? "Khác",
                    Level = job.Level.ToString(),
                    SalaryMin = job.SalaryMin ?? 0.0,
                    SalaryMax = job.SalaryMax ?? 0.0,
                    IsNegotiable = job.IsSalaryNegotiable,
                    SalaryCurrency = job.SalaryCurrency ?? "USD"
                };
                await _publishEndpoint.Publish(evt);
            }
        }
        catch (Exception ex)
        {
            System.Console.WriteLine($"Error publishing JobPublishedEvent: {ex.Message}");
        }
    }
}

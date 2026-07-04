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

using Microsoft.AspNetCore.Http;
using CommonService.Import;
using CommonService.Caching;

namespace JobService.Services;

public class JobServiceImpl : IJobService
{
    private readonly IJobRepository   _jobRepo;
    private readonly ISkillRepository _skillRepo;
    private readonly IMapper          _mapper;
    private readonly IPublishEndpoint _publishEndpoint;
    private readonly MinioSettings      _minioSettings;
    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly IExcelCsvImportService _importService;
    private readonly ICacheService          _cacheService;
    private const string CACHE_KEY_STATS = "jobs:category-stats";

    public JobServiceImpl(
        IJobRepository jobRepo, 
        ISkillRepository skillRepo, 
        IMapper mapper,
        IPublishEndpoint publishEndpoint,
        IOptions<MinioSettings> minioSettings,
        IHttpContextAccessor httpContextAccessor,
        IExcelCsvImportService importService,
        ICacheService cacheService)
    {
        _jobRepo         = jobRepo;
        _skillRepo       = skillRepo;
        _mapper          = mapper;
        _publishEndpoint = publishEndpoint;
        _minioSettings   = minioSettings.Value;
        _httpContextAccessor = httpContextAccessor;
        _importService   = importService;
        _cacheService    = cacheService;
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
        var cached = await _cacheService.GetAsync<List<JobCategoryStatResponse>>(CACHE_KEY_STATS);
        if (cached != null) return cached;

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

        await _cacheService.SetAsync(CACHE_KEY_STATS, result, TimeSpan.FromMinutes(30));

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

        await _cacheService.RemoveAsync(CACHE_KEY_STATS);

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

        await _cacheService.RemoveAsync(CACHE_KEY_STATS);
        await _cacheService.RemoveAsync($"job_skills:{id}");

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

        await _cacheService.RemoveAsync(CACHE_KEY_STATS);
        await _cacheService.RemoveAsync($"job_skills:{id}");
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

        await _cacheService.RemoveAsync(CACHE_KEY_STATS);
        await _cacheService.RemoveAsync($"job_skills:{id}");

        await PublishJobPublishedEventAsync(id);

        return FormatUrls(_mapper.Map<JobResponse>(job));
    }

    private async Task<int> ParseYearsOfExperienceAsync(string? exp)
    {
        if (string.IsNullOrWhiteSpace(exp)) return 0;

        int FallbackParse(string text)
        {
            var expLower = text.ToLower();
            if (expLower.Contains("dưới 1 năm") || 
                expLower.Contains("không yêu cầu") || 
                expLower.Contains("chấp nhận fresher") || 
                expLower.Contains("không có kinh nghiệm") ||
                expLower.Contains("no experience") ||
                expLower.Contains("under 1 year"))
            {
                return 0;
            }
            var match = System.Text.RegularExpressions.Regex.Match(text, @"\d+");
            if (match.Success && int.TryParse(match.Value, out var years))
            {
                return years;
            }
            return 0;
        }

        try
        {
            bool inDocker = Environment.GetEnvironmentVariable("RUNNING_IN_DOCKER") == "true";
            string url = inDocker 
                ? "http://cvintelligenceservice:5006/api/v1/cv/parse-experience" 
                : "http://localhost:5006/api/v1/cv/parse-experience";

            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(5) };
            var payload = new { experience_text = exp };
            var content = new StringContent(
                System.Text.Json.JsonSerializer.Serialize(payload), 
                System.Text.Encoding.UTF8, 
                "application/json"
            );

            var response = await client.PostAsync(url, content);
            if (response.IsSuccessStatusCode)
            {
                var responseString = await response.Content.ReadAsStringAsync();
                using var doc = System.Text.Json.JsonDocument.Parse(responseString);
                if (doc.RootElement.TryGetProperty("years", out var yearsProp))
                {
                    return yearsProp.GetInt32();
                }
            }
        }
        catch (Exception ex)
        {
            System.Console.WriteLine($"[LLM Exp Parser] Error calling CVIntelligenceService: {ex.Message}. Using regex fallback.");
        }

        return FallbackParse(exp);
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
                    YearsOfExperience = await ParseYearsOfExperienceAsync(job.ExperienceRequired),
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

    public async Task<ImportResult<ImportJobDto>> ImportAsync(IFormFile file)
    {
        var importResult = await _importService.ImportAsync<ImportJobDto>(file);
        if (!importResult.IsSuccess)
        {
            return importResult;
        }

        var validatedList = new List<ImportJobDto>();
        var seenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        // Environment URLs
        var inDocker = Environment.GetEnvironmentVariable("RUNNING_IN_DOCKER") == "true";
        var authUrl = inDocker ? "http://authservice:8080" : "http://localhost:5001";
        var companyUrl = inDocker ? "http://companyservice:8080" : "http://localhost:5003";

        // Get auth token from request to forward to authservice
        var authHeader = _httpContextAccessor.HttpContext?.Request.Headers["Authorization"].ToString();

        using var client = new HttpClient();
        if (!string.IsNullOrEmpty(authHeader))
        {
            client.DefaultRequestHeaders.Add("Authorization", authHeader);
        }

        // Preload skills catalog to avoid N+1 DB calls
        var allSkills = await _skillRepo.GetAllAsync();
        var skillDict = allSkills
            .Where(s => !s.IsDeleted)
            .ToDictionary(s => s.Name.Trim().ToLower(), s => s);

        // Mapped entity objects
        var mappedJobs = new List<(Job Job, List<Skill> Skills)>();

        for (int i = 0; i < importResult.Data.Count; i++)
        {
            var req = importResult.Data[i];
            var rowIndex = i + 2;

            if (req == null) continue;

            // 1. Basic validation
            if (string.IsNullOrWhiteSpace(req.Name))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "Name", ErrorMessage = "Tên tin tuyển dụng không được để trống." });
                continue;
            }

            var name = req.Name.Trim();
            if (seenNames.Contains(name))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "Name", ErrorMessage = $"Tên tin tuyển dụng '{req.Name}' bị trùng lặp trong file." });
                continue;
            }
            seenNames.Add(name);

            if (string.IsNullOrWhiteSpace(req.CompanyName))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "CompanyName", ErrorMessage = "Tên công ty không được để trống." });
                continue;
            }

            if (string.IsNullOrWhiteSpace(req.HREmail))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "HREmail", ErrorMessage = "Email nhà tuyển dụng không được để trống." });
                continue;
            }

            // 2. Validate salary
            if (req.SalaryMin.HasValue && req.SalaryMin.Value < 0)
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "SalaryMin", ErrorMessage = "Lương tối thiểu không được âm." });
                continue;
            }
            if (req.SalaryMax.HasValue && req.SalaryMax.Value < 0)
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "SalaryMax", ErrorMessage = "Lương tối đa không được âm." });
                continue;
            }
            if (req.SalaryMin.HasValue && req.SalaryMax.HasValue && req.SalaryMax.Value < req.SalaryMin.Value)
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "SalaryMax", ErrorMessage = "Lương tối đa phải lớn hơn hoặc bằng lương tối thiểu." });
                continue;
            }

            // 3. Validate Quantity
            if (req.Quantity <= 0)
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "Quantity", ErrorMessage = "Số lượng tuyển dụng phải lớn hơn 0." });
                continue;
            }

            // 4. Validate Level and JobType
            if (!Enum.TryParse<JobLevel>(req.Level.Trim(), true, out var parsedLevel))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "Level", ErrorMessage = $"Cấp độ '{req.Level}' không hợp lệ. Cho phép: INTERN, FRESHER, JUNIOR, MIDDLE, SENIOR, LEADER, MANAGER." });
                continue;
            }

            if (!Enum.TryParse<JobType>(req.JobType.Trim(), true, out var parsedJobType))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "JobType", ErrorMessage = $"Loại hình '{req.JobType}' không hợp lệ. Cho phép: FULL_TIME, PART_TIME, REMOTE, HYBRID, INTERNSHIP." });
                continue;
            }

            // 5. Query Company from CompanyService
            Guid companyId = Guid.Empty;
            string? companyLogoUrl = null;
            try
            {
                var searchCompUrl = $"{companyUrl}/api/v1/companies?searchTerm={Uri.EscapeDataString(req.CompanyName.Trim())}&pageSize=20";
                var compRes = await client.GetFromJsonAsync<ApiResponseHelper<CompanySearchResponse>>(searchCompUrl);
                var matchedCompany = compRes?.Data?.Result?
                    .FirstOrDefault(c => c.Name.Trim().Equals(req.CompanyName.Trim(), StringComparison.OrdinalIgnoreCase));

                if (matchedCompany == null)
                {
                    importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "CompanyName", ErrorMessage = $"Không tìm thấy công ty '{req.CompanyName}' trong hệ thống." });
                    continue;
                }
                companyId = matchedCompany.Id;
                companyLogoUrl = matchedCompany.Logo;
            }
            catch (Exception ex)
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "CompanyName", ErrorMessage = $"Lỗi khi xác thực công ty: {ex.Message}" });
                continue;
            }

            // 6. Query HR from AuthService
            Guid hrCustomerId = Guid.Empty;
            try
            {
                var searchUserUrl = $"{authUrl}/api/v1/users?searchTerm={Uri.EscapeDataString(req.HREmail.Trim())}&pageSize=20";
                var userRes = await client.GetFromJsonAsync<ApiResponseHelper<UserSearchResponse>>(searchUserUrl);
                var matchedUser = userRes?.Data?.Result?
                    .FirstOrDefault(u => u.Email.Trim().Equals(req.HREmail.Trim(), StringComparison.OrdinalIgnoreCase));

                if (matchedUser == null)
                {
                    importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "HREmail", ErrorMessage = $"Không tìm thấy tài khoản với email '{req.HREmail}' trong hệ thống." });
                    continue;
                }
                if (matchedUser.Role == null || !matchedUser.Role.Name.Equals("HR", StringComparison.OrdinalIgnoreCase))
                {
                    importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "HREmail", ErrorMessage = $"Tài khoản '{req.HREmail}' không phải là nhà tuyển dụng (HR)." });
                    continue;
                }
                hrCustomerId = matchedUser.Id;
            }
            catch (Exception ex)
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "HREmail", ErrorMessage = $"Lỗi khi xác thực tài khoản nhà tuyển dụng: {ex.Message}" });
                continue;
            }

            // 7. Validate skills
            var jobSkillsList = new List<Skill>();
            var skillsFailed = false;
            if (!string.IsNullOrWhiteSpace(req.Skills))
            {
                var skillsToParse = req.Skills.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
                foreach (var skName in skillsToParse)
                {
                    if (skillDict.TryGetValue(skName.ToLower(), out var skillObj))
                    {
                        jobSkillsList.Add(skillObj);
                    }
                    else
                    {
                        importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "Skills", ErrorMessage = $"Kỹ năng '{skName}' không tồn tại trong hệ thống." });
                        skillsFailed = true;
                    }
                }
            }
            if (skillsFailed) continue;

            // Row is valid! Map it
            var newJob = new Job
            {
                CustomerId = hrCustomerId,
                CompanyId = companyId,
                Name = req.Name.Trim(),
                CompanyName = req.CompanyName.Trim(),
                CompanyLogo = companyLogoUrl,
                Location = req.Location,
                SalaryMin = req.SalaryMin,
                SalaryMax = req.SalaryMax,
                SalaryCurrency = req.SalaryCurrency,
                IsSalaryNegotiable = req.IsSalaryNegotiable,
                Quantity = req.Quantity,
                Level = parsedLevel,
                JobType = parsedJobType,
                ExperienceRequired = req.ExperienceRequired,
                Description = req.Description,
                Requirements = req.Requirements,
                Benefits = req.Benefits,
                StartDate = DateTime.UtcNow,
                EndDate = DateTime.UtcNow.AddDays(30), // Default 30 days
                Status = JobStatus.PUBLISHED, // Import directly to published
                Category = req.Category
            };

            mappedJobs.Add((newJob, jobSkillsList));
            validatedList.Add(req);
        }

        if (!importResult.IsSuccess)
        {
            importResult.Data.Clear();
            return importResult;
        }

        // Atomic transaction import
        foreach (var (job, skills) in mappedJobs)
        {
            await _jobRepo.AddAsync(job);
            
            // Assign JobSkills
            if (skills.Any())
            {
                job.JobSkills = skills.Select(s => new JobSkill
                {
                    JobId = job.Id,
                    SkillId = s.Id
                }).ToList();
            }
        }
        await _jobRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_STATS);

        // Trigger events for search indexing
        foreach (var (job, _) in mappedJobs)
        {
            await PublishJobPublishedEventAsync(job.Id);
        }

        importResult.Data = validatedList;
        return importResult;
    }
}

public class ApiResponseHelper<T>
{
    public int StatusCode { get; set; }
    public string? Error { get; set; }
    public string? Message { get; set; }
    public DataHelper<T>? Data { get; set; }
}

public class DataHelper<T>
{
    public List<T> Result { get; set; } = new();
}

public class CompanySearchResponse
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Logo { get; set; }
}

public class UserSearchResponse
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public RoleHelper? Role { get; set; }
}

public class RoleHelper
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
}

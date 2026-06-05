using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using CommonService.Import;
using JobService.Models;
using JobService.Models.Request;
using JobService.Models.Response;
using JobService.Repositories.Interface;
using JobService.Services.Interface;
using JobService.Specifications;
using MassTransit;
using Microsoft.AspNetCore.Http;

namespace JobService.Services;

public class SkillServiceImpl : ISkillService
{
    private readonly ISkillRepository       _skillRepo;
    private readonly IMapper                _mapper;
    private readonly IPublishEndpoint       _publishEndpoint;
    private readonly IExcelCsvImportService _importService;

    public SkillServiceImpl(
        ISkillRepository skillRepo, 
        IMapper mapper, 
        IPublishEndpoint publishEndpoint,
        IExcelCsvImportService importService)
    {
        _skillRepo       = skillRepo;
        _mapper          = mapper;
        _publishEndpoint = publishEndpoint;
        _importService   = importService;
    }

    public async Task<ResultPaginationDto<SkillResponse>> GetAllAsync(
        string? searchTerm, string? sortBy, bool isDescending, int pageNumber, int pageSize)
    {
        var spec      = new SkillFilterSpec(searchTerm, sortBy, isDescending, pageNumber, pageSize);
        var countSpec = new SkillFilterCountSpec(searchTerm);

        var items = await _skillRepo.ListAsync(spec);
        var total = await _skillRepo.CountAsync(countSpec);

        return new ResultPaginationDto<SkillResponse>(
            _mapper.Map<List<SkillResponse>>(items),
            pageNumber, pageSize, total);
    }

    public async Task<SkillResponse> GetByIdAsync(Guid id)
    {
        var skill = await _skillRepo.GetByIdAsync(id);
        if (skill == null || skill.IsDeleted)
            throw new NotFoundException($"Không tìm thấy kỹ năng với ID: {id}");

        return _mapper.Map<SkillResponse>(skill);
    }

    public async Task<SkillResponse> CreateAsync(CreateSkillRequest request)
    {
        var existing = await _skillRepo.GetByNameAsync(request.Name);
        if (existing != null)
            throw new BadRequestException($"Kỹ năng '{request.Name}' đã tồn tại.");

        var skill = _mapper.Map<Skill>(request);
        await _skillRepo.AddAsync(skill);
        await _skillRepo.SaveChangesAsync();

        // Publish event to RabbitMQ for ProfileService to sync
        await _publishEndpoint.Publish(new CommonService.Events.SkillCreatedEvent
        {
            Id   = skill.Id,
            Name = skill.Name
        });

        return _mapper.Map<SkillResponse>(skill);
    }

    public async Task<SkillResponse> UpdateAsync(Guid id, UpdateSkillRequest request)
    {
        var skill = await _skillRepo.GetByIdAsync(id);
        if (skill == null || skill.IsDeleted)
            throw new NotFoundException($"Không tìm thấy kỹ năng với ID: {id}");

        var conflict = await _skillRepo.GetByNameAsync(request.Name);
        if (conflict != null && conflict.Id != id)
            throw new BadRequestException($"Kỹ năng '{request.Name}' đã tồn tại.");

        skill.Name = request.Name;
        _skillRepo.Update(skill);
        await _skillRepo.SaveChangesAsync();

        // Publish event to RabbitMQ for ProfileService to sync
        await _publishEndpoint.Publish(new CommonService.Events.SkillUpdatedEvent
        {
            Id   = skill.Id,
            Name = skill.Name
        });

        return _mapper.Map<SkillResponse>(skill);
    }

    public async Task DeleteAsync(Guid id)
    {
        var skill = await _skillRepo.GetByIdAsync(id);
        if (skill == null || skill.IsDeleted)
            throw new NotFoundException($"Không tìm thấy kỹ năng với ID: {id}");

        _skillRepo.Delete(skill);
        await _skillRepo.SaveChangesAsync();

        // Publish event to RabbitMQ for ProfileService to sync
        await _publishEndpoint.Publish(new CommonService.Events.SkillDeletedEvent
        {
            Id = skill.Id
        });
    }

    public async Task<ImportResult<CreateSkillRequest>> ImportAsync(IFormFile file)
    {
        var importResult = await _importService.ImportAsync<CreateSkillRequest>(file);
        if (!importResult.IsSuccess)
        {
            return importResult;
        }

        // Validate duplicates and empty rows in memory and db
        var validatedList = new List<CreateSkillRequest>();
        var seenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (int i = 0; i < importResult.Data.Count; i++)
        {
            var req = importResult.Data[i];
            var rowIndex = i + 2;

            if (req == null || string.IsNullOrWhiteSpace(req.Name))
            {
                importResult.Errors.Add(new ValidationError
                {
                    RowIndex = rowIndex,
                    ColumnName = "Name",
                    ErrorMessage = "Tên kỹ năng không được để trống."
                });
                continue;
            }

            var trimmedName = req.Name.Trim();
            if (seenNames.Contains(trimmedName))
            {
                importResult.Errors.Add(new ValidationError
                {
                    RowIndex = rowIndex,
                    ColumnName = "Name",
                    ErrorMessage = $"Tên kỹ năng '{req.Name}' bị lặp lại trong file import."
                });
                continue;
            }

            seenNames.Add(trimmedName);

            var existing = await _skillRepo.GetByNameAsync(trimmedName);
            if (existing != null)
            {
                importResult.Errors.Add(new ValidationError
                {
                    RowIndex = rowIndex,
                    ColumnName = "Name",
                    ErrorMessage = $"Kỹ năng '{req.Name}' đã tồn tại trong hệ thống."
                });
                continue;
            }

            req.Name = trimmedName;
            validatedList.Add(req);
        }

        if (!importResult.IsSuccess)
        {
            importResult.Data.Clear();
            return importResult;
        }

        // Save to Database and publish sync events
        foreach (var req in validatedList)
        {
            var skill = _mapper.Map<Skill>(req);
            await _skillRepo.AddAsync(skill);

            // Publish event to RabbitMQ for ProfileService to sync
            await _publishEndpoint.Publish(new CommonService.Events.SkillCreatedEvent
            {
                Id   = skill.Id,
                Name = skill.Name
            });
        }
        await _skillRepo.SaveChangesAsync();

        importResult.Data = validatedList;
        return importResult;
    }
}

public class SavedJobServiceImpl : ISavedJobService
{
    private readonly ISavedJobRepository _savedRepo;
    private readonly IJobRepository      _jobRepo;
    private readonly IMapper             _mapper;

    public SavedJobServiceImpl(ISavedJobRepository savedRepo, IJobRepository jobRepo, IMapper mapper)
    {
        _savedRepo = savedRepo;
        _jobRepo   = jobRepo;
        _mapper    = mapper;
    }

    public async Task<ResultPaginationDto<SavedJobResponse>> GetSavedJobsAsync(Guid customerId, int pageNumber, int pageSize)
    {
        var saved = await _savedRepo.GetByCustomerAsync(customerId, pageNumber, pageSize);
        var total = await _savedRepo.CountByCustomerAsync(customerId);
        return new ResultPaginationDto<SavedJobResponse>(
            _mapper.Map<List<SavedJobResponse>>(saved),
            pageNumber, pageSize, total);
    }

    public async Task SaveAsync(Guid jobId, Guid customerId, string? note)
    {
        var job = await _jobRepo.GetByIdAsync(jobId);
        if (job == null || job.IsDeleted)
            throw new NotFoundException($"Không tìm thấy tin tuyển dụng với ID: {jobId}");

        var existing = await _savedRepo.GetAsync(jobId, customerId);
        if (existing != null)
            throw new BadRequestException("Tin tuyển dụng này đã được lưu rồi.");

        await _savedRepo.AddAsync(new SavedJob
        {
            JobId      = jobId,
            CustomerId = customerId,
            SavedAt    = DateTimeOffset.UtcNow,
            Note       = note
        });
        await _savedRepo.SaveChangesAsync();
    }

    public async Task UnsaveAsync(Guid jobId, Guid customerId)
    {
        var saved = await _savedRepo.GetAsync(jobId, customerId);
        if (saved == null)
            throw new NotFoundException("Không tìm thấy tin đã lưu này.");

        _savedRepo.Delete(saved);
        await _savedRepo.SaveChangesAsync();
    }
}

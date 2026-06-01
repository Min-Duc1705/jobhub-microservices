using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using ResumeService.Models;
using ResumeService.Models.Request;
using ResumeService.Models.Response;
using ResumeService.Repositories.Interface;
using ResumeService.Services.Interface;
using ResumeService.Specifications;

namespace ResumeService.Services;

public class ResumeServiceImpl : IResumeService
{
    private readonly IResumeRepository _resumeRepo;
    private readonly IMapper           _mapper;

    public ResumeServiceImpl(IResumeRepository resumeRepo, IMapper mapper)
    {
        _resumeRepo = resumeRepo;
        _mapper     = mapper;
    }

    public async Task<ResultPaginationDto<ResumeResponse>> GetAllAsync(ResumeFilterRequest filter)
    {
        var spec = new ResumeFilterSpec(
            filter.SearchTerm, filter.CustomerId, filter.IsDefault,
            filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);

        var countSpec = new ResumeFilterCountSpec(
            filter.SearchTerm, filter.CustomerId, filter.IsDefault);

        var items = await _resumeRepo.ListAsync(spec);
        var total = await _resumeRepo.CountAsync(countSpec);

        return new ResultPaginationDto<ResumeResponse>(
            _mapper.Map<List<ResumeResponse>>(items),
            filter.PageNumber, filter.PageSize, total);
    }

    public async Task<ResumeResponse> GetByIdAsync(Guid id)
    {
        var spec   = new ResumeByIdSpec(id);
        var resume = await _resumeRepo.GetEntityWithSpec(spec);

        if (resume == null)
            throw new NotFoundException($"Không tìm thấy CV với ID: {id}");

        return _mapper.Map<ResumeResponse>(resume);
    }

    public async Task<ResumeResponse> CreateAsync(Guid customerId, CreateResumeRequest request)
    {
        var resume = _mapper.Map<Resume>(request);
        resume.CustomerId = customerId;

        if (request.IsDefault)
            await _resumeRepo.SetDefaultAsync(customerId, Guid.Empty);

        await _resumeRepo.AddAsync(resume);
        await _resumeRepo.SaveChangesAsync();

        if (request.IsDefault)
            await _resumeRepo.SetDefaultAsync(customerId, resume.Id);

        return _mapper.Map<ResumeResponse>(resume);
    }

    public async Task<ResumeResponse> UpdateAsync(Guid id, UpdateResumeRequest request)
    {
        var resume = await _resumeRepo.GetByIdAsync(id);
        if (resume == null || resume.IsDeleted)
            throw new NotFoundException($"Không tìm thấy CV với ID: {id}");

        _mapper.Map(request, resume);

        if (request.IsDefault == true)
            await _resumeRepo.SetDefaultAsync(resume.CustomerId, id);

        _resumeRepo.Update(resume);
        await _resumeRepo.SaveChangesAsync();

        return _mapper.Map<ResumeResponse>(resume);
    }

    public async Task DeleteAsync(Guid id)
    {
        var resume = await _resumeRepo.GetByIdAsync(id);
        if (resume == null || resume.IsDeleted)
            throw new NotFoundException($"Không tìm thấy CV với ID: {id}");

        _resumeRepo.Delete(resume);
        await _resumeRepo.SaveChangesAsync();
    }

    public async Task SetDefaultAsync(Guid customerId, Guid resumeId)
    {
        var resume = await _resumeRepo.GetByIdAsync(resumeId);
        if (resume == null || resume.IsDeleted)
            throw new NotFoundException($"Không tìm thấy CV với ID: {resumeId}");

        if (resume.CustomerId != customerId)
            throw new BadRequestException("CV này không thuộc về bạn.");

        await _resumeRepo.SetDefaultAsync(customerId, resumeId);
    }

    // ── Online CV Builder ──────────────────────────────────────────────────────

    public async Task<ResumeResponse> CreateOnlineAsync(Guid customerId, CreateOnlineCvRequest request)
    {
        var resume = new Resume
        {
            CustomerId  = customerId,
            Title       = request.Title,
            IsOnlineCv  = true,
            TemplateId  = request.TemplateId,
            ContentJson = request.ContentJson,
            IsDefault   = request.IsDefault,
        };

        if (request.IsDefault)
            await _resumeRepo.SetDefaultAsync(customerId, Guid.Empty);

        await _resumeRepo.AddAsync(resume);
        await _resumeRepo.SaveChangesAsync();

        if (request.IsDefault)
            await _resumeRepo.SetDefaultAsync(customerId, resume.Id);

        return _mapper.Map<ResumeResponse>(resume);
    }

    public async Task<ResumeResponse> UpdateContentAsync(Guid id, Guid customerId, UpdateCvContentRequest request)
    {
        var resume = await _resumeRepo.GetByIdAsync(id);
        if (resume == null || resume.IsDeleted)
            throw new NotFoundException($"Không tìm thấy CV với ID: {id}");

        if (resume.CustomerId != customerId)
            throw new BadRequestException("CV này không thuộc về bạn.");

        if (!resume.IsOnlineCv)
            throw new BadRequestException("CV này không phải Online CV.");

        if (request.Title       != null) resume.Title       = request.Title;
        if (request.TemplateId  != null) resume.TemplateId  = request.TemplateId;
        if (request.ContentJson != null) resume.ContentJson = request.ContentJson;

        if (request.IsDefault == true)
            await _resumeRepo.SetDefaultAsync(customerId, id);

        _resumeRepo.Update(resume);
        await _resumeRepo.SaveChangesAsync();

        return _mapper.Map<ResumeResponse>(resume);
    }
}

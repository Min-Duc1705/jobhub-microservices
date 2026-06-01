using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using ResumeService.Models;
using ResumeService.Models.Enums;
using ResumeService.Models.Request;
using ResumeService.Models.Response;
using ResumeService.Repositories.Interface;
using ResumeService.Services.Interface;
using ResumeService.Specifications;
using MassTransit;
using CommonService.Events;

namespace ResumeService.Services;

public class ApplicationServiceImpl : IApplicationService
{
    private readonly IApplicationRepository _appRepo;
    private readonly IResumeRepository      _resumeRepo;
    private readonly IMapper                _mapper;
    private readonly IPublishEndpoint       _publishEndpoint;

    public ApplicationServiceImpl(
        IApplicationRepository appRepo,
        IResumeRepository resumeRepo,
        IMapper mapper,
        IPublishEndpoint publishEndpoint)
    {
        _appRepo         = appRepo;
        _resumeRepo      = resumeRepo;
        _mapper          = mapper;
        _publishEndpoint = publishEndpoint;
    }

    public async Task<ResultPaginationDto<ApplicationResponse>> GetAllAsync(ApplicationFilterRequest filter)
    {
        var spec = new ApplicationFilterSpec(
            filter.CustomerId, filter.JobId, filter.Status,
            filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);

        var countSpec = new ApplicationFilterCountSpec(
            filter.CustomerId, filter.JobId, filter.Status);

        var items = await _appRepo.ListAsync(spec);
        var total = await _appRepo.CountAsync(countSpec);

        return new ResultPaginationDto<ApplicationResponse>(
            _mapper.Map<List<ApplicationResponse>>(items),
            filter.PageNumber, filter.PageSize, total);
    }

    public async Task<ApplicationResponse> GetByIdAsync(Guid id)
    {
        var spec = new ApplicationByIdSpec(id);
        var app  = await _appRepo.GetEntityWithSpec(spec);

        if (app == null)
            throw new NotFoundException($"Không tìm thấy đơn ứng tuyển với ID: {id}");

        return _mapper.Map<ApplicationResponse>(app);
    }

    public async Task<ApplicationResponse> CreateAsync(Guid customerId, CreateApplicationRequest request)
    {
        // Kiểm tra đã ứng tuyển Job này chưa
        var exists = await _appRepo.ExistsAsync(customerId, request.JobId);
        if (exists)
            throw new BadRequestException("Bạn đã ứng tuyển cho tin tuyển dụng này rồi.");

        // Kiểm tra Resume có tồn tại và thuộc về ứng viên
        var resume = await _resumeRepo.GetByIdAsync(request.ResumeId);
        if (resume == null || resume.IsDeleted)
            throw new NotFoundException($"Không tìm thấy CV với ID: {request.ResumeId}");

        if (resume.CustomerId != customerId)
            throw new BadRequestException("CV này không thuộc về bạn.");

        var application = _mapper.Map<Application>(request);
        application.CustomerId = customerId;
        application.Status     = ApplicationStatus.PENDING;

        await _appRepo.AddAsync(application);
        await _appRepo.SaveChangesAsync();

        await _publishEndpoint.Publish(new ApplicationSubmittedEvent
        {
            ApplicationId = application.Id,
            CustomerId = customerId,
            JobId = application.JobId,
            SubmittedAt = application.CreatedDate.DateTime
        });

        return await GetByIdAsync(application.Id);
    }

    public async Task<ApplicationResponse> ChangeStatusAsync(Guid id, UpdateApplicationStatusRequest request)
    {
        var app = await _appRepo.GetByIdAsync(id);
        if (app == null || app.IsDeleted)
            throw new NotFoundException($"Không tìm thấy đơn ứng tuyển với ID: {id}");

        app.Status     = request.Status;
        app.ReviewNote = request.ReviewNote;

        _appRepo.Update(app);
        await _appRepo.SaveChangesAsync();

        await _publishEndpoint.Publish(new ApplicationStatusChangedEvent
        {
            ApplicationId = app.Id,
            CustomerId = app.CustomerId,
            JobId = app.JobId,
            Status = app.Status.ToString(),
            ReviewNote = app.ReviewNote
        });

        return await GetByIdAsync(id);
    }

    public async Task DeleteAsync(Guid id, Guid customerId)
    {
        var app = await _appRepo.GetByIdAsync(id);
        if (app == null || app.IsDeleted)
            throw new NotFoundException($"Không tìm thấy đơn ứng tuyển với ID: {id}");

        if (app.CustomerId != customerId)
            throw new BadRequestException("Bạn không có quyền hủy đơn ứng tuyển này.");

        if (app.Status != ApplicationStatus.PENDING)
            throw new BadRequestException("Chỉ có thể hủy đơn ứng tuyển đang ở trạng thái chờ duyệt (PENDING).");

        _appRepo.Delete(app);
        await _appRepo.SaveChangesAsync();
    }
}

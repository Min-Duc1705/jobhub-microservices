using CommonService.Common;
using ResumeService.Models.Request;
using ResumeService.Models.Response;

namespace ResumeService.Services.Interface;

public interface IApplicationService
{
    Task<ResultPaginationDto<ApplicationResponse>> GetAllAsync(ApplicationFilterRequest filter);
    Task<ApplicationResponse> GetByIdAsync(Guid id);
    Task<ApplicationResponse> CreateAsync(Guid customerId, CreateApplicationRequest request);
    Task<ApplicationResponse> ChangeStatusAsync(Guid id, UpdateApplicationStatusRequest request);
    Task DeleteAsync(Guid id, Guid customerId);
}

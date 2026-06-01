using CommonService.Common;
using ResumeService.Models.Request;
using ResumeService.Models.Response;

namespace ResumeService.Services.Interface;

public interface IResumeService
{
    Task<ResultPaginationDto<ResumeResponse>> GetAllAsync(ResumeFilterRequest filter);
    Task<ResumeResponse> GetByIdAsync(Guid id);
    Task<ResumeResponse> CreateAsync(Guid customerId, CreateResumeRequest request);
    Task<ResumeResponse> UpdateAsync(Guid id, UpdateResumeRequest request);
    Task DeleteAsync(Guid id);
    Task SetDefaultAsync(Guid customerId, Guid resumeId);

    // ── Online CV Builder ──────────────────────────────────────────────────────
    Task<ResumeResponse> CreateOnlineAsync(Guid customerId, CreateOnlineCvRequest request);
    Task<ResumeResponse> UpdateContentAsync(Guid id, Guid customerId, UpdateCvContentRequest request);
}

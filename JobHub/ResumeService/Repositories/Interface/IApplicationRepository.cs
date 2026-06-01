using CommonService.Repository;
using ResumeService.Models;

namespace ResumeService.Repositories.Interface;

public interface IApplicationRepository : IGenericRepository<Application>
{
    /// <summary>Kiểm tra ứng viên đã ứng tuyển Job này chưa (tránh trùng).</summary>
    Task<bool> ExistsAsync(Guid customerId, Guid jobId);
}

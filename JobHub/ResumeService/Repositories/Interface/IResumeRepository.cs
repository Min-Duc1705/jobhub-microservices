using CommonService.Repository;
using ResumeService.Models;

namespace ResumeService.Repositories.Interface;

public interface IResumeRepository : IGenericRepository<Resume>
{
    /// <summary>Lấy CV mặc định của ứng viên.</summary>
    Task<Resume?> GetDefaultByCustomerAsync(Guid customerId);

    /// <summary>Bỏ CV mặc định cũ rồi set CV mới làm mặc định.</summary>
    Task SetDefaultAsync(Guid customerId, Guid resumeId);
}

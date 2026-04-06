using AuthService.Models;
using CommonService.Repository;

namespace AuthService.Repositories.Interface
{
    /// <summary>
    /// Kế thừa IGenericRepository để có CRUD + Specification.
    /// Permission được quản lý static (seed data), ít thay đổi runtime.
    /// </summary>
    public interface IPermissionRepository : IGenericRepository<Permission>
    {
        /// <summary>Tìm Permission theo ApiPath + Method (unique composite).</summary>
        Task<Permission?> GetByPathAndMethodAsync(string apiPath, string method);

        /// <summary>Lấy danh sách Permission theo nhiều IDs (dùng khi gán vào Role).</summary>
        Task<List<Permission>> GetPermissionsByIdsAsync(IEnumerable<Guid> ids);

        /// <summary>Lấy tất cả Permissions theo Module.</summary>
        Task<IEnumerable<Permission>> GetByModuleAsync(string module);

        /// <summary>Lấy danh sách dropdown (không phân trang).</summary>
        Task<IEnumerable<Permission>> GetAllDropdownAsync();
    }
}

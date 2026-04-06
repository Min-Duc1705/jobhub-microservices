using AuthService.Models;
using CommonService.Repository;

namespace AuthService.Repositories.Interface
{
    /// <summary>
    /// Kế thừa IGenericRepository để có CRUD + Specification.
    /// Role chủ yếu đọc (GetAll, GetById), ít khi tạo/sửa/xóa trong runtime.
    /// </summary>
    public interface IRoleRepository : IGenericRepository<Role>
    {
        /// <summary>Tìm Role theo tên (unique).</summary>
        Task<Role?> GetByNameAsync(string name);

        /// <summary>Lấy Role kèm theo danh sách Permissions (tracking — để EF update M-N).</summary>
        Task<Role?> GetWithPermissionsAsync(Guid roleId);

        /// <summary>Lấy tất cả roles active — chỉ Id + Name, dành cho dropdown/select.</summary>
        Task<List<Role>> GetAllDropdownAsync();

        /// <summary>
        /// Lấy email của tất cả users đang dùng Role này.
        /// Dùng để xóa Redis permission cache khi Role thay đổi permissions.
        /// </summary>
        Task<List<string>> GetUserEmailsByRoleIdAsync(Guid roleId);
    }
}

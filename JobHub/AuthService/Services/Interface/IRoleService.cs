using AuthService.Models.Request;
using AuthService.Models.Response;
using CommonService.Common;

namespace AuthService.Services.Interface
{
    public interface IRoleService
    {
        Task<ResultPaginationDto<RoleResponse>> GetAllRolesAsync(RoleFilterRequest filter);
        Task<RoleResponse>          GetRoleByIdAsync(Guid id);
        Task<RoleResponse>          CreateRoleAsync(CreateRoleRequest request);
        Task<RoleResponse>          UpdateRoleAsync(Guid id, UpdateRoleRequest request);
        Task DeleteRoleAsync(Guid id);
        Task<List<RoleDropdownDto>> GetDropdownAsync();
    }
}

using AuthService.Models.Request;
using AuthService.Models.Response;
using CommonService.Common;

namespace AuthService.Services.Interface
{
    public interface IPermissionService
    {
        Task<ResultPaginationDto<PermissionResponse>> GetAllPermissionsAsync(PermissionFilterRequest filter);
        Task<PermissionResponse>          GetPermissionByIdAsync(Guid id);
        Task<PermissionResponse>          CreatePermissionAsync(CreatePermissionRequest request);
        Task<PermissionResponse>          UpdatePermissionAsync(Guid id, UpdatePermissionRequest request);
        Task DeletePermissionAsync(Guid id);
        Task<List<PermissionResponse>>    GetDropdownAsync();
    }
}

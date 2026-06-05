using AuthService.Models.Request;
using AuthService.Models.Response;
using CommonService.Common;

namespace AuthService.Services.Interface
{
    public interface IUserService
    {
        Task<ResultPaginationDto<UserResponse>> GetAllUsersAsync(UserFilterRequest filter);
        Task<UserResponse>  GetUserByIdAsync(Guid id);
        Task<UserResponse>  CreateUserAsync(CreateUserRequest request);
        Task<UserResponse>  UpdateUserAsync(Guid id, UpdateUserRequest request);
        Task DeleteUserAsync(Guid id);
        Task ResetPasswordAsync(Guid id, ResetPasswordRequest request);
        Task BroadcastNotificationAsync(BroadcastNotificationRequest request);
        Task<CommonService.Import.ImportResult<ImportUserDto>> ImportAsync(Microsoft.AspNetCore.Http.IFormFile file);
    }
}

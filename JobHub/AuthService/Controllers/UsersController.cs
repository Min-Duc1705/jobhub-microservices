using AuthService.Models.Request;
using AuthService.Models.Response;
using AuthService.Services.Interface;
using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AuthService.Controllers;

[ApiController]
[Route("api/v1/users")]
[Authorize]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;

    public UsersController(IUserService userService)
    {
        _userService = userService;
    }

    // GET /api/v1/users?searchTerm=john&status=Active&roleId=...&pageNumber=1&pageSize=10
    [HttpGet]
    [ApiMessage("Lấy danh sách user thành công")]
    [RequiresPermission("GET", "/api/v1/users")]
    public async Task<ActionResult<ResultPaginationDto<UserResponse>>> GetAll([FromQuery] UserFilterRequest filter)
    {
        var result = await _userService.GetAllUsersAsync(filter);
        return Ok(result);
    }

    // GET /api/v1/users/{id}
    [HttpGet("{id:guid}")]
    [ApiMessage("Lấy thông tin user thành công")]
    [RequiresPermission("GET", "/api/v1/users/{id}")]
    public async Task<ActionResult<UserResponse>> GetById(Guid id)
    {
        var user = await _userService.GetUserByIdAsync(id);
        return Ok(user);
    }

    // POST /api/v1/users
    [HttpPost]
    [ApiMessage("Tạo user mới thành công")]
    [RequiresPermission("POST", "/api/v1/users")]
    public async Task<ActionResult<UserResponse>> Create([FromBody] CreateUserRequest request)
    {
        var user = await _userService.CreateUserAsync(request);
        return StatusCode(201, user);
    }

    // PUT /api/v1/users/{id}
    [HttpPut("{id:guid}")]
    [ApiMessage("Cập nhật user thành công")]
    [RequiresPermission("PUT", "/api/v1/users/{id}")]
    public async Task<ActionResult<UserResponse>> Update(Guid id, [FromBody] UpdateUserRequest request)
    {
        var user = await _userService.UpdateUserAsync(id, request);
        return Ok(user);
    }

    // DELETE /api/v1/users/{id}
    [HttpDelete("{id:guid}")]
    [ApiMessage("Xóa user thành công")]
    [RequiresPermission("DELETE", "/api/v1/users/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _userService.DeleteUserAsync(id);
        return Ok(null);
    }

    // PATCH /api/v1/users/{id}/reset-password
    [HttpPatch("{id:guid}/reset-password")]
    [ApiMessage("Đặt lại mật khẩu thành công")]
    [RequiresPermission("PATCH", "/api/v1/users/{id}/reset-password")]
    public async Task<IActionResult> ResetPassword(Guid id, [FromBody] ResetPasswordRequest request)
    {
        await _userService.ResetPasswordAsync(id, request);
        return Ok(null);
    }
}

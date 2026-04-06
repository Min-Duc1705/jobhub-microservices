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
[Route("api/v1/roles")]
[Authorize]
public class RolesController : ControllerBase
{
    private readonly IRoleService _roleService;

    public RolesController(IRoleService roleService)
    {
        _roleService = roleService;
    }

    // GET /api/v1/roles?searchTerm=Admin&isActive=true&pageNumber=1&pageSize=10
    [HttpGet]
    [ApiMessage("Lấy danh sách role thành công")]
    [RequiresPermission("GET", "/api/v1/roles")]
    public async Task<ActionResult<ResultPaginationDto<RoleResponse>>> GetAll([FromQuery] RoleFilterRequest filter)
    {
        var result = await _roleService.GetAllRolesAsync(filter);
        return Ok(result);
    }

    // GET /api/v1/roles/dropdown — chỉ {id, name} cho select/dropdown
    [HttpGet("dropdown")]
    [ApiMessage("Lấy danh sách role (dropdown) thành công")]
    public async Task<ActionResult<List<RoleDropdownDto>>> GetDropdown()
    {
        // Dropdown endpoint không cần permission check (mọi user đã login đều dùng)
        var result = await _roleService.GetDropdownAsync();
        return Ok(result);
    }

    // GET /api/v1/roles/{id}
    [HttpGet("{id:guid}")]
    [ApiMessage("Lấy thông tin role thành công")]
    [RequiresPermission("GET", "/api/v1/roles/{id}")]
    public async Task<ActionResult<RoleResponse>> GetById(Guid id)
    {
        var role = await _roleService.GetRoleByIdAsync(id);
        return Ok(role);
    }

    // POST /api/v1/roles
    [HttpPost]
    [ApiMessage("Tạo role mới thành công")]
    [RequiresPermission("POST", "/api/v1/roles")]
    public async Task<ActionResult<RoleResponse>> Create([FromBody] CreateRoleRequest request)
    {
        var role = await _roleService.CreateRoleAsync(request);
        return StatusCode(201, role);
    }

    // PUT /api/v1/roles/{id}
    [HttpPut("{id:guid}")]
    [ApiMessage("Cập nhật role thành công")]
    [RequiresPermission("PUT", "/api/v1/roles/{id}")]
    public async Task<ActionResult<RoleResponse>> Update(Guid id, [FromBody] UpdateRoleRequest request)
    {
        var role = await _roleService.UpdateRoleAsync(id, request);
        return Ok(role);
    }

    // DELETE /api/v1/roles/{id}
    [HttpDelete("{id:guid}")]
    [ApiMessage("Xóa role thành công")]
    [RequiresPermission("DELETE", "/api/v1/roles/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _roleService.DeleteRoleAsync(id);
        return Ok(null);
    }
}

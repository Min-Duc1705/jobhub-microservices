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
[Route("api/v1/permissions")]
[Authorize]
public class PermissionsController : ControllerBase
{
    private readonly IPermissionService _permissionService;

    public PermissionsController(IPermissionService permissionService)
    {
        _permissionService = permissionService;
    }

    // GET /api/v1/permissions?searchTerm=job&module=JOB&method=GET
    [HttpGet]
    [ApiMessage("Lấy danh sách permission thành công")]
    [RequiresPermission("GET", "/api/v1/permissions")]
    public async Task<ActionResult<ResultPaginationDto<PermissionResponse>>> GetAll([FromQuery] PermissionFilterRequest filter)
    {
        var result = await _permissionService.GetAllPermissionsAsync(filter);
        return Ok(result);
    }

    // GET /api/v1/permissions/dropdown
    [HttpGet("dropdown")]
    [ApiMessage("Lấy danh sách dropdown permission thành công")]
    public async Task<ActionResult<List<PermissionResponse>>> GetDropdown()
    {
        var result = await _permissionService.GetDropdownAsync();
        return Ok(result);
    }

    // GET /api/v1/permissions/{id}
    [HttpGet("{id:guid}")]
    [ApiMessage("Lấy thông tin permission thành công")]
    [RequiresPermission("GET", "/api/v1/permissions/{id}")]
    public async Task<ActionResult<PermissionResponse>> GetById(Guid id)
    {
        var perm = await _permissionService.GetPermissionByIdAsync(id);
        return Ok(perm);
    }

    // POST /api/v1/permissions
    [HttpPost]
    [ApiMessage("Tạo permission mới thành công")]
    [RequiresPermission("POST", "/api/v1/permissions")]
    public async Task<ActionResult<PermissionResponse>> Create([FromBody] CreatePermissionRequest request)
    {
        var perm = await _permissionService.CreatePermissionAsync(request);
        return StatusCode(201, perm);
    }

    // PUT /api/v1/permissions/{id}
    [HttpPut("{id:guid}")]
    [ApiMessage("Cập nhật permission thành công")]
    [RequiresPermission("PUT", "/api/v1/permissions/{id}")]
    public async Task<ActionResult<PermissionResponse>> Update(Guid id, [FromBody] UpdatePermissionRequest request)
    {
        var perm = await _permissionService.UpdatePermissionAsync(id, request);
        return Ok(perm);
    }

    // DELETE /api/v1/permissions/{id}
    [HttpDelete("{id:guid}")]
    [ApiMessage("Xóa permission thành công")]
    [RequiresPermission("DELETE", "/api/v1/permissions/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _permissionService.DeletePermissionAsync(id);
        return Ok(null);
    }
}

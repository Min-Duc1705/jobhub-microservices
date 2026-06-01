using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using ResumeService.Models.Request;
using ResumeService.Models.Response;
using ResumeService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace ResumeService.Controllers;

[ApiController]
[Route("api/v1/applications")]
public class ApplicationsController : ControllerBase
{
    private readonly IApplicationService _applicationService;

    public ApplicationsController(IApplicationService applicationService)
        => _applicationService = applicationService;

    // GET /api/v1/applications (lọc theo customerId, jobId, status)
    [HttpGet]
    [Authorize]
    [ApiMessage("Lấy danh sách đơn ứng tuyển thành công")]
    [RequiresPermission("GET", "/api/v1/applications")]
    public async Task<ActionResult<ResultPaginationDto<ApplicationResponse>>> GetAll(
        [FromQuery] ApplicationFilterRequest filter)
        => Ok(await _applicationService.GetAllAsync(filter));

    // GET /api/v1/applications/{id}
    [HttpGet("{id:guid}")]
    [Authorize]
    [ApiMessage("Lấy thông tin đơn ứng tuyển thành công")]
    [RequiresPermission("GET", "/api/v1/applications/{id}")]
    public async Task<ActionResult<ApplicationResponse>> GetById(Guid id)
        => Ok(await _applicationService.GetByIdAsync(id));

    // POST /api/v1/applications (Ứng viên nộp đơn)
    [HttpPost]
    [Authorize]
    [ApiMessage("Nộp đơn ứng tuyển thành công")]
    [RequiresPermission("POST", "/api/v1/applications")]
    public async Task<ActionResult<ApplicationResponse>> Create([FromBody] CreateApplicationRequest request)
    {
        var customerId = GetCurrentUserId();
        var result = await _applicationService.CreateAsync(customerId, request);
        return StatusCode(201, result);
    }

    // PATCH /api/v1/applications/{id}/status (NTD duyệt / từ chối)
    [HttpPatch("{id:guid}/status")]
    [Authorize]
    [ApiMessage("Cập nhật trạng thái đơn ứng tuyển thành công")]
    [RequiresPermission("PATCH", "/api/v1/applications/{id}/status")]
    public async Task<ActionResult<ApplicationResponse>> ChangeStatus(
        Guid id, [FromBody] UpdateApplicationStatusRequest request)
        => Ok(await _applicationService.ChangeStatusAsync(id, request));

    // DELETE /api/v1/applications/{id}
    [HttpDelete("{id:guid}")]
    [Authorize]
    [ApiMessage("Hủy đơn ứng tuyển thành công")]
    [RequiresPermission("DELETE", "/api/v1/applications/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        var customerId = GetCurrentUserId();
        await _applicationService.DeleteAsync(id, customerId);
        return Ok((object?)null);
    }

    // ── Helper ────────────────────────────────────────────────────────────────
    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không xác định được người dùng.");
        return Guid.Parse(sub);
    }
}

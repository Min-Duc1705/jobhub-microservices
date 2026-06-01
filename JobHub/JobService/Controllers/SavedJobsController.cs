using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using JobService.Models.Response;
using JobService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace JobService.Controllers;

[ApiController]
[Route("api/v1/saved-jobs")]
[Authorize]
public class SavedJobsController : ControllerBase
{
    private readonly ISavedJobService _savedJobService;

    public SavedJobsController(ISavedJobService savedJobService) => _savedJobService = savedJobService;

    // GET /api/v1/saved-jobs (danh sách job đã lưu của current user)
    [HttpGet]
    [ApiMessage("Lấy danh sách việc làm đã lưu thành công")]
    [RequiresPermission("GET", "/api/v1/saved-jobs")]
    public async Task<ActionResult<ResultPaginationDto<SavedJobResponse>>> GetMySavedJobs(
        [FromQuery] int pageNumber = 1,
        [FromQuery] int pageSize = 10)
    {
        var customerId = GetCurrentUserId();
        return Ok(await _savedJobService.GetSavedJobsAsync(customerId, pageNumber, pageSize));
    }

    // POST /api/v1/saved-jobs/{jobId}
    [HttpPost("{jobId:guid}")]
    [ApiMessage("Lưu tin tuyển dụng thành công")]
    [RequiresPermission("POST", "/api/v1/saved-jobs/{jobId}")]
    public async Task<IActionResult> Save(Guid jobId, [FromQuery] string? note)
    {
        var customerId = GetCurrentUserId();
        await _savedJobService.SaveAsync(jobId, customerId, note);
        return Ok((object?)null);
    }

    // DELETE /api/v1/saved-jobs/{jobId}
    [HttpDelete("{jobId:guid}")]
    [ApiMessage("Bỏ lưu tin tuyển dụng thành công")]
    [RequiresPermission("DELETE", "/api/v1/saved-jobs/{jobId}")]
    public async Task<IActionResult> Unsave(Guid jobId)
    {
        var customerId = GetCurrentUserId();
        await _savedJobService.UnsaveAsync(jobId, customerId);
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

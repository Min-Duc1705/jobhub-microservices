using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using JobService.Models.Request;
using JobService.Models.Response;
using JobService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace JobService.Controllers;

[ApiController]
[Route("api/v1/jobs")]
public class JobsController : ControllerBase
{
    private readonly IJobService _jobService;

    public JobsController(IJobService jobService) => _jobService = jobService;

    // GET /api/v1/jobs (public)
    [HttpGet]
    [AllowAnonymous]
    [ApiMessage("Lấy danh sách tin tuyển dụng thành công")]
    public async Task<ActionResult<ResultPaginationDto<JobResponse>>> GetAll(
        [FromQuery] JobFilterRequest filter)
        => Ok(await _jobService.GetAllAsync(filter));

    // GET /api/v1/jobs/{id} (public, tăng ViewCount)
    [HttpGet("{id:guid}")]
    [AllowAnonymous]
    [ApiMessage("Lấy thông tin tin tuyển dụng thành công")]
    public async Task<ActionResult<JobResponse>> GetById(Guid id)
        => Ok(await _jobService.GetByIdAsync(id, incrementView: true));

    // POST /api/v1/jobs (HR)
    [HttpPost]
    [Authorize]
    [ApiMessage("Tạo tin tuyển dụng thành công")]
    [RequiresPermission("POST", "/api/v1/jobs")]
    public async Task<ActionResult<JobResponse>> Create([FromBody] CreateJobRequest request)
    {
        var customerId = GetCurrentUserId();
        var result = await _jobService.CreateAsync(customerId, request);
        return StatusCode(201, result);
    }

    // PUT /api/v1/jobs/{id} (HR)
    [HttpPut("{id:guid}")]
    [Authorize]
    [ApiMessage("Cập nhật tin tuyển dụng thành công")]
    [RequiresPermission("PUT", "/api/v1/jobs/{id}")]
    public async Task<ActionResult<JobResponse>> Update(Guid id, [FromBody] UpdateJobRequest request)
        => Ok(await _jobService.UpdateAsync(id, request));

    // DELETE /api/v1/jobs/{id} (HR / Admin)
    [HttpDelete("{id:guid}")]
    [Authorize]
    [ApiMessage("Xóa tin tuyển dụng thành công")]
    [RequiresPermission("DELETE", "/api/v1/jobs/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _jobService.DeleteAsync(id);
        return Ok((object?)null);
    }

    // PATCH /api/v1/jobs/{id}/status?status=PUBLISHED (HR / Admin)
    [HttpPatch("{id:guid}/status")]
    [Authorize]
    [ApiMessage("Cập nhật trạng thái tin tuyển dụng thành công")]
    [RequiresPermission("PATCH", "/api/v1/jobs/{id}/status")]
    public async Task<ActionResult<JobResponse>> ChangeStatus(Guid id, [FromQuery] string status)
        => Ok(await _jobService.ChangeStatusAsync(id, status));

    // GET /api/v1/jobs/{id}/preview (AllowAnonymous — HR preview trước khi publish, không tăng ViewCount)
    [HttpGet("{id:guid}/preview")]
    [AllowAnonymous]
    [ApiMessage("Lấy bản xem trước tin tuyển dụng thành công")]
    public async Task<ActionResult<JobResponse>> Preview(Guid id)
        => Ok(await _jobService.GetByIdAsync(id, incrementView: false));

    // GET /api/v1/jobs/stats/categories
    [HttpGet("stats/categories")]
    [Authorize]
    [ApiMessage("Lấy thống kê ngành nghề tin tuyển dụng thành công")]
    public async Task<ActionResult<List<JobCategoryStatResponse>>> GetCategoryStats()
        => Ok(await _jobService.GetJobCategoryStatsAsync());

    // ── Helper ────────────────────────────────────────────────────────────────
    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không xác định được người dùng.");
        return Guid.Parse(sub);
    }
}

using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using JobService.Models.Request;
using JobService.Models.Response;
using JobService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace JobService.Controllers;

/// <summary>
/// API dành riêng cho Admin — lấy tất cả jobs không bị ép filter PUBLISHED.
/// Route: GET /api/v1/admin/jobs
/// </summary>
[ApiController]
[Route("api/v1/admin/jobs")]
[Authorize]
public class AdminJobsController : ControllerBase
{
    private readonly IJobService _jobService;

    public AdminJobsController(IJobService jobService) => _jobService = jobService;

    /// <summary>
    /// Lấy toàn bộ danh sách jobs (admin) — không bị ép filter status PUBLISHED,
    /// có thể lọc theo status, searchTerm, v.v.
    /// </summary>
    [HttpGet]
    [RequiresPermission("GET", "/api/v1/admin/jobs")]
    [ApiMessage("Lấy danh sách tin tuyển dụng (admin) thành công")]
    public async Task<ActionResult<ResultPaginationDto<JobResponse>>> GetAllForAdmin(
        [FromQuery] AdminJobFilterRequest filter)
        => Ok(await _jobService.GetAllForAdminAsync(filter));
}

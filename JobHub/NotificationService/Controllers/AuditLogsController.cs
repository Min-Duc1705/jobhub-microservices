using System.Threading.Tasks;
using CommonService.Annotations;
using CommonService.Common;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NotificationService.Models;
using NotificationService.Services.Interface;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/audit-logs")]
[Authorize]
public class AuditLogsController : ControllerBase
{
    private readonly IAuditLogService _auditLogService;

    public AuditLogsController(IAuditLogService auditLogService)
    {
        _auditLogService = auditLogService;
    }

    [HttpGet]
    [ApiMessage("Lấy danh sách audit log thành công")]
    public async Task<ActionResult<ResultPaginationDto<AuditLog>>> GetAuditLogs(
        [FromQuery] string? searchTerm = null,
        [FromQuery] string? action = null,
        [FromQuery] string? entityName = null,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10)
    {
        var result = await _auditLogService.GetAuditLogsAsync(searchTerm, action, entityName, page, pageSize);
        return Ok(result);
    }
}

using CommonService.Common;
using NotificationService.Models;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Interface;
using System.Threading.Tasks;

namespace NotificationService.Services;

public class AuditLogServiceImpl : IAuditLogService
{
    private readonly IAuditLogRepository _auditLogRepo;

    public AuditLogServiceImpl(IAuditLogRepository auditLogRepo)
    {
        _auditLogRepo = auditLogRepo;
    }

    public async Task<ResultPaginationDto<AuditLog>> GetAuditLogsAsync(
        string? searchTerm,
        string? action,
        string? entityName,
        int page,
        int pageSize)
    {
        return await _auditLogRepo.GetAuditLogsAsync(searchTerm, action, entityName, page, pageSize);
    }
}

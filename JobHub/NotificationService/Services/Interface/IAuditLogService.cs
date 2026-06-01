using CommonService.Common;
using NotificationService.Models;
using System.Threading.Tasks;

namespace NotificationService.Services.Interface;

public interface IAuditLogService
{
    Task<ResultPaginationDto<AuditLog>> GetAuditLogsAsync(
        string? searchTerm,
        string? action,
        string? entityName,
        int page,
        int pageSize);
}

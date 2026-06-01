using CommonService.Repository;
using NotificationService.Models;
using System.Threading.Tasks;
using CommonService.Common;

namespace NotificationService.Repositories.Interface;

public interface IAuditLogRepository : IGenericRepository<AuditLog>
{
    Task<ResultPaginationDto<AuditLog>> GetAuditLogsAsync(
        string? searchTerm,
        string? action,
        string? entityName,
        int page,
        int pageSize);
}

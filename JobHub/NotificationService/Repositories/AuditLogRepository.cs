using CommonService.Repository;
using Microsoft.EntityFrameworkCore;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Repositories.Interface;
using System.Linq;
using System.Threading.Tasks;
using CommonService.Common;

namespace NotificationService.Repositories;

public class AuditLogRepository : GenericRepository<NotificationDbContext, AuditLog>, IAuditLogRepository
{
    public AuditLogRepository(NotificationDbContext dbContext) : base(dbContext)
    {
    }

    public async Task<ResultPaginationDto<AuditLog>> GetAuditLogsAsync(
        string? searchTerm,
        string? action,
        string? entityName,
        int page,
        int pageSize)
    {
        if (page < 1) page = 1;
        if (pageSize < 1) pageSize = 10;
        if (pageSize > 100) pageSize = 100;

        var query = _dbSet.AsNoTracking().AsQueryable();

        if (!string.IsNullOrEmpty(searchTerm))
        {
            var lowerSearch = searchTerm.ToLower();
            query = query.Where(a => 
                (a.Email != null && a.Email.ToLower().Contains(lowerSearch)) ||
                (a.Username != null && a.Username.ToLower().Contains(lowerSearch)) ||
                (a.Action != null && a.Action.ToLower().Contains(lowerSearch)) ||
                (a.EntityName != null && a.EntityName.ToLower().Contains(lowerSearch)) ||
                (a.EntityId != null && a.EntityId.ToLower().Contains(lowerSearch)) ||
                (a.ChangesJson != null && a.ChangesJson.ToLower().Contains(lowerSearch))
            );
        }

        if (!string.IsNullOrEmpty(action))
        {
            query = query.Where(a => a.Action != null && a.Action.ToLower() == action.ToLower());
        }

        if (!string.IsNullOrEmpty(entityName))
        {
            query = query.Where(a => a.EntityName != null && a.EntityName.ToLower() == entityName.ToLower());
        }

        query = query.OrderByDescending(a => a.Timestamp);

        var totalRecords = await query.CountAsync();
        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        return new ResultPaginationDto<AuditLog>(items, page, pageSize, totalRecords);
    }
}

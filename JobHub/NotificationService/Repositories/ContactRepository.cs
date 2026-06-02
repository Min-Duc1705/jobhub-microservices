using CommonService.Repository;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Repositories.Interface;
using CommonService.Common;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using System.Threading.Tasks;

namespace NotificationService.Repositories;

public class ContactRepository : GenericRepository<NotificationDbContext, Contact>, IContactRepository
{
    public ContactRepository(NotificationDbContext dbContext) : base(dbContext)
    {
    }

    public async Task<ResultPaginationDto<Contact>> GetContactsAsync(
        string? searchTerm,
        string? topic,
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
            query = query.Where(c =>
                c.FullName.ToLower().Contains(lowerSearch) ||
                c.Email.ToLower().Contains(lowerSearch) ||
                (c.Phone != null && c.Phone.ToLower().Contains(lowerSearch)) ||
                c.Message.ToLower().Contains(lowerSearch)
            );
        }

        if (!string.IsNullOrEmpty(topic))
        {
            query = query.Where(c => c.Topic.ToLower() == topic.ToLower());
        }

        query = query.OrderByDescending(c => c.CreatedAt);

        var totalRecords = await query.CountAsync();
        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        return new ResultPaginationDto<Contact>(items, page, pageSize, totalRecords);
    }
}

using CommonService.Repository;
using Microsoft.EntityFrameworkCore;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Repositories.Interface;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace NotificationService.Repositories;

public class NotificationRepository : GenericRepository<NotificationDbContext, Notification>, INotificationRepository
{
    public NotificationRepository(NotificationDbContext dbContext) : base(dbContext)
    {
    }

    public async Task<List<Notification>> GetUserNotificationsAsync(Guid userId)
    {
        return await _dbSet
            .Where(n => n.AppUserId == userId && !n.IsDeleted)
            .OrderByDescending(n => n.CreatedDate)
            .ToListAsync();
    }
}

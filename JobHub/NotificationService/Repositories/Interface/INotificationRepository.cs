using CommonService.Repository;
using NotificationService.Models;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Repositories.Interface;

public interface INotificationRepository : IGenericRepository<Notification>
{
    Task<List<Notification>> GetUserNotificationsAsync(Guid userId);
}

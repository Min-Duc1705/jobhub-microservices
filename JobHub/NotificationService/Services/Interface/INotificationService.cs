using NotificationService.Models;
using NotificationService.Models.Response;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Services.Interface;

public interface INotificationService
{
    Task<List<NotificationResponse>> GetUserNotificationsAsync(Guid userId);
    Task<NotificationResponse> MarkAsReadAsync(Guid id, Guid userId);
    Task MarkAllAsReadAsync(Guid userId);
    Task<Notification> CreateNotificationAsync(Guid userId, string title, string message, string type);
}

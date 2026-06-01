using AutoMapper;
using CommonService.Exceptions;
using NotificationService.Models;
using NotificationService.Models.Response;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Services;

public class NotificationServiceImpl : INotificationService
{
    private readonly INotificationRepository _notificationRepo;
    private readonly IMapper _mapper;

    public NotificationServiceImpl(INotificationRepository notificationRepo, IMapper mapper)
    {
        _notificationRepo = notificationRepo;
        _mapper = mapper;
    }

    public async Task<List<NotificationResponse>> GetUserNotificationsAsync(Guid userId)
    {
        var list = await _notificationRepo.GetUserNotificationsAsync(userId);
        return _mapper.Map<List<NotificationResponse>>(list);
    }

    public async Task<NotificationResponse> MarkAsReadAsync(Guid id, Guid userId)
    {
        var notif = await _notificationRepo.GetByIdAsync(id);
        if (notif == null || notif.IsDeleted)
            throw new NotFoundException("Không tìm thấy thông báo.");

        if (notif.AppUserId != userId)
            throw new BadRequestException("Bạn không có quyền đọc thông báo này.");

        notif.IsRead = true;
        _notificationRepo.Update(notif);
        await _notificationRepo.SaveChangesAsync();

        return _mapper.Map<NotificationResponse>(notif);
    }

    public async Task MarkAllAsReadAsync(Guid userId)
    {
        var list = await _notificationRepo.GetUserNotificationsAsync(userId);
        var unread = list.FindAll(n => !n.IsRead);
        
        foreach (var notif in unread)
        {
            notif.IsRead = true;
            _notificationRepo.Update(notif);
        }

        if (unread.Count > 0)
        {
            await _notificationRepo.SaveChangesAsync();
        }
    }

    public async Task<Notification> CreateNotificationAsync(Guid userId, string title, string message, string type)
    {
        var notif = new Notification
        {
            AppUserId = userId,
            Title = title,
            Message = message,
            Type = type,
            IsRead = false,
            CreatedDate = DateTimeOffset.UtcNow,
            CreatedBy = "system"
        };

        await _notificationRepo.AddAsync(notif);
        await _notificationRepo.SaveChangesAsync();

        return notif;
    }
}

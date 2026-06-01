using CommonService.Events;
using MassTransit;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Logging;
using NotificationService.Hubs;
using NotificationService.Services.Interface;
using System.Threading.Tasks;

namespace NotificationService.Consumers;

public class SendNotificationConsumer : IConsumer<SendNotificationEvent>
{
    private readonly INotificationService _notificationService;
    private readonly IHubContext<NotificationHub> _hubContext;
    private readonly ILogger<SendNotificationConsumer> _logger;

    public SendNotificationConsumer(
        INotificationService notificationService,
        IHubContext<NotificationHub> hubContext,
        ILogger<SendNotificationConsumer> logger)
    {
        _notificationService = notificationService;
        _hubContext = hubContext;
        _logger = logger;
    }

    public async Task Consume(ConsumeContext<SendNotificationEvent> context)
    {
        var msg = context.Message;
        _logger.LogInformation("Nhận SendNotificationEvent cho User {UserId}: {Title}", msg.UserId, msg.Title);

        var notification = await _notificationService.CreateNotificationAsync(
            msg.UserId, msg.Title, msg.Message, msg.Type);

        var payload = new
        {
            id = notification.Id.ToString(),
            title = notification.Title,
            message = notification.Message,
            isRead = notification.IsRead,
            createdDate = notification.CreatedDate,
            type = notification.Type
        };

        await _hubContext.Clients.Group(msg.UserId.ToString().ToLower())
            .SendAsync("ReceiveNotification", payload);

        _logger.LogInformation("Đã lưu (qua service) và đẩy notification {Id} thành công qua SignalR cho User {UserId}", notification.Id, msg.UserId);
    }
}

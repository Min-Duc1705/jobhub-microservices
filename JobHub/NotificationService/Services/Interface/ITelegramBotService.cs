using System;
using System.Threading.Tasks;
using Telegram.Bot.Types;

namespace NotificationService.Services.Interface;

public interface ITelegramBotService
{
    Task ProcessUpdateAsync(Update update);
    Task SendPushNotificationAsync(Guid userId, string title, string message);
}

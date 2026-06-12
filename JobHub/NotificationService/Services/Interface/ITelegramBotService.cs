using System;
using System.Threading.Tasks;
using Telegram.Bot.Types;

namespace NotificationService.Services.Interface;

public interface ITelegramBotService
{
    Task ProcessUpdateAsync(Update update, string? botToken = null);
    Task SendPushNotificationAsync(Guid userId, string title, string message);
    Task SendTextMessageAsync(Guid userId, string message);
    Task<string?> GetSystemBotUsernameAsync();
}

using System;

namespace NotificationService.Models;

public class UserTelegramBinding
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    public long? TelegramChatId { get; set; }
    public string? Username { get; set; }
    public string? BotToken { get; set; }
    public string? BotUsername { get; set; }
    public DateTimeOffset CreatedDate { get; set; } = DateTimeOffset.UtcNow;
}

using System;

namespace NotificationService.Models.Response;

public class MessageResponse
{
    public Guid Id { get; set; }
    public Guid ConversationId { get; set; }
    public string SenderId { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Type { get; set; } = "text";
    public bool IsRead { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
}

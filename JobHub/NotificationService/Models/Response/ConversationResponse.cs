using System;

namespace NotificationService.Models.Response;

public class ConversationResponse
{
    public Guid Id { get; set; }
    public string ParticipantA { get; set; } = string.Empty;
    public string ParticipantB { get; set; } = string.Empty;
    public string? LastMessageContent { get; set; }
    public DateTimeOffset? LastMessageAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
    public int UnreadCount { get; set; }
}

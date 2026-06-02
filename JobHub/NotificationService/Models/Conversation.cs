using System;
using CommonService.Models;
using CommonService.Models.Interface;

namespace NotificationService.Models;

public class Conversation : EntityBase<Guid>, ISoftDelete
{
    public string ParticipantA { get; set; } = string.Empty;
    public string ParticipantB { get; set; } = string.Empty;
    public string? LastMessageContent { get; set; }
    public DateTimeOffset? LastMessageAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    // ISoftDelete members
    public bool IsDeleted { get; set; } = false;
    public DateTimeOffset? DeletedAt { get; set; }
}

using System;
using CommonService.Models;
using CommonService.Models.Interface;

namespace NotificationService.Models;

public class Message : EntityBase<Guid>, ISoftDelete
{
    public Guid ConversationId { get; set; }
    public string SenderId { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Type { get; set; } = "text"; // text, image, file
    public bool IsRead { get; set; } = false;
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    // Navigation property
    public Conversation? Conversation { get; set; }

    // ISoftDelete members
    public bool IsDeleted { get; set; } = false;
    public DateTimeOffset? DeletedAt { get; set; }
}

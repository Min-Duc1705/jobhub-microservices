using System;

namespace NotificationService.Models.Response;

public class NotificationResponse
{
    public Guid Id { get; set; }
    public Guid AppUserId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string Type { get; set; } = "default";
    public bool IsRead { get; set; }
    public DateTimeOffset CreatedDate { get; set; }
}

using System;
using CommonService.Models;

namespace NotificationService.Models;

public class Notification : EntityAuditableBase<Guid>
{
    public Guid AppUserId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string Type { get; set; } = "default"; // view | invite | recommend | default
    public bool IsRead { get; set; } = false;
}

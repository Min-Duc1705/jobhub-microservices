using System;
using CommonService.Models;

namespace NotificationService.Models;

public class InterviewGoogleEvent : EntityBase<Guid>
{
    public Guid InterviewId { get; set; }
    public string GoogleEventId { get; set; } = string.Empty;
    public string RecruiterId { get; set; } = string.Empty;
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}

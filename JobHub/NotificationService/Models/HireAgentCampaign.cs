using System;
using CommonService.Models;
using CommonService.Models.Interface;

namespace NotificationService.Models;

public class HireAgentCampaign : EntityBase<Guid>, ISoftDelete
{
    public Guid JobId { get; set; }
    public string JobName { get; set; } = string.Empty;
    public string JobDescription { get; set; } = string.Empty;
    public string RecruiterId { get; set; } = string.Empty;
    public int TargetCount { get; set; } = 5;
    public string Status { get; set; } = "Active"; // Active, Paused, Completed
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    // ISoftDelete members
    public bool IsDeleted { get; set; } = false;
    public DateTimeOffset? DeletedAt { get; set; }
}

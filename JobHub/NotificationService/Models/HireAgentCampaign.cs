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
    /// <summary>Tỉnh/thành phố job (empty = không giới hạn địa lý)</summary>
    public string? JobLocation { get; set; }
    /// <summary>Loại hình: REMOTE/HYBRID/FULL_TIME/... (REMOTE+HYBRID = bỏ qua check location)</summary>
    public string? JobType { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    // ISoftDelete members
    public bool IsDeleted { get; set; } = false;
    public DateTimeOffset? DeletedAt { get; set; }
}

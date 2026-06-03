using System;

namespace NotificationService.Models.Request;

public class CreateHireAgentCampaignRequest
{
    public Guid JobId { get; set; }
    public string JobName { get; set; } = string.Empty;
    public string JobDescription { get; set; } = string.Empty;
    public int TargetCount { get; set; } = 5;
    /// <summary>Tỉnh/thành phố của job (VD: "Hồ Chí Minh", "Hà Nội")</summary>
    public string? JobLocation { get; set; }
    /// <summary>Loại hình làm việc: REMOTE, HYBRID, FULL_TIME, PART_TIME, INTERNSHIP</summary>
    public string? JobType { get; set; }
}

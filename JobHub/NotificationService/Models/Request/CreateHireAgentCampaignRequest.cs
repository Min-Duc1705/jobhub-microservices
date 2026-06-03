using System;

namespace NotificationService.Models.Request;

public class CreateHireAgentCampaignRequest
{
    public Guid JobId { get; set; }
    public string JobName { get; set; } = string.Empty;
    public string JobDescription { get; set; } = string.Empty;
    public int TargetCount { get; set; } = 5;
}

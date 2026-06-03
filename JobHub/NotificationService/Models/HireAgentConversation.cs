using System;
using CommonService.Models;
using CommonService.Models.Interface;

namespace NotificationService.Models;

public class HireAgentConversation : EntityBase<Guid>, ISoftDelete
{
    public Guid CampaignId { get; set; }
    public Guid ConversationId { get; set; }
    public string CandidateId { get; set; } = string.Empty;
    public string CvText { get; set; } = string.Empty;
    public string Status { get; set; } = "Screening"; // Screening, Passed, Failed, Scheduled
    public DateTimeOffset LastQuestionAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? InterviewDate { get; set; }

    // ISoftDelete members
    public bool IsDeleted { get; set; } = false;
    public DateTimeOffset? DeletedAt { get; set; }
}

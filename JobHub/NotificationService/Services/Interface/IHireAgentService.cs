using NotificationService.Models;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Services.Interface;

public interface IHireAgentService
{
    Task<HireAgentCampaign> CreateCampaignAsync(Guid jobId, string jobName, string jobDescription, string recruiterId, int targetCount, string? jobLocation = null, string? jobType = null);
    Task<List<HireAgentCampaign>> GetCampaignsByRecruiterAsync(string recruiterId);
    Task<List<HireAgentConversation>> GetConversationsByCampaignAsync(Guid campaignId);
    Task RunCampaignOutreachAsync(Guid campaignId);
    Task ProcessCandidateReplyAsync(Guid chatConversationId, string candidateMessage);
    Task<HireAgentCampaign?> GetCampaignByIdAsync(Guid campaignId);

    /// <summary>HR đề xuất ngày phỏng vấn → status chuyển sang PendingCandidateConfirm</summary>
    Task<HireAgentConversation> ScheduleInterviewAsync(Guid campaignId, string candidateId, DateTimeOffset interviewDate);

    /// <summary>Candidate xác nhận đồng ý → status chuyển sang Scheduled → gửi email xác nhận chính thức</summary>
    Task<HireAgentConversation> ConfirmInterviewAsync(Guid campaignId, string candidateId);

    /// <summary>Candidate đề xuất đổi lịch → thông báo HR, reset về Passed</summary>
    Task<HireAgentConversation> ProposeRescheduleAsync(Guid campaignId, string candidateId, string? message = null);

    Task<HireAgentConversation?> GetConversationByCandidateAndCampaignAsync(Guid campaignId, string candidateId);
}

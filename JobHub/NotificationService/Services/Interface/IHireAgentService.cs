using NotificationService.Models;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Services.Interface;

public interface IHireAgentService
{
    Task<HireAgentCampaign> CreateCampaignAsync(Guid jobId, string jobName, string jobDescription, string recruiterId, int targetCount);
    Task<List<HireAgentCampaign>> GetCampaignsByRecruiterAsync(string recruiterId);
    Task<List<HireAgentConversation>> GetConversationsByCampaignAsync(Guid campaignId);
    Task RunCampaignOutreachAsync(Guid campaignId);
    Task ProcessCandidateReplyAsync(Guid chatConversationId, string candidateMessage);
    Task<HireAgentCampaign?> GetCampaignByIdAsync(Guid campaignId);
    Task<HireAgentConversation> ScheduleInterviewAsync(Guid campaignId, string candidateId, DateTimeOffset interviewDate);
}

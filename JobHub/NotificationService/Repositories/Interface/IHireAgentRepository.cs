using CommonService.Repository;
using NotificationService.Models;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Repositories.Interface;

public interface IHireAgentRepository : IGenericRepository<HireAgentCampaign>
{
    Task<HireAgentCampaign?> GetCampaignAsync(Guid campaignId);
    Task<List<HireAgentCampaign>> GetActiveCampaignsAsync();
    Task<List<HireAgentCampaign>> GetCampaignsByRecruiterAsync(string recruiterId);
    Task<List<HireAgentConversation>> GetConversationsByCampaignAsync(Guid campaignId);
    Task<HireAgentConversation?> GetConversationByCandidateAndCampaignAsync(string candidateId, Guid campaignId);
    Task<HireAgentConversation?> GetActiveConversationByChatIdAsync(Guid chatConversationId);
    Task CreateCampaignAsync(HireAgentCampaign campaign);
    Task UpdateCampaignAsync(HireAgentCampaign campaign);
    Task CreateConversationAsync(HireAgentConversation conversation);
    Task UpdateConversationAsync(HireAgentConversation conversation);
    Task<List<HireAgentConversation>> GetConversationsByCandidateAsync(string candidateId);
}

using CommonService.Repository;
using Microsoft.EntityFrameworkCore;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Repositories.Interface;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace NotificationService.Repositories;

public class HireAgentRepository : GenericRepository<NotificationDbContext, HireAgentCampaign>, IHireAgentRepository
{
    private readonly NotificationDbContext _dbContext;

    public HireAgentRepository(NotificationDbContext dbContext) : base(dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<HireAgentCampaign?> GetCampaignAsync(Guid campaignId)
    {
        return await _dbSet.AsNoTracking().FirstOrDefaultAsync(c => c.Id == campaignId);
    }

    public async Task<List<HireAgentCampaign>> GetActiveCampaignsAsync()
    {
        return await _dbSet.Where(c => c.Status == "Active").ToListAsync();
    }

    public async Task<List<HireAgentCampaign>> GetCampaignsByRecruiterAsync(string recruiterId)
    {
        return await _dbSet.Where(c => c.RecruiterId == recruiterId).OrderByDescending(c => c.CreatedAt).ToListAsync();
    }

    public async Task<List<HireAgentConversation>> GetConversationsByCampaignAsync(Guid campaignId)
    {
        return await _dbContext.HireAgentConversations
            .Where(c => c.CampaignId == campaignId)
            .OrderByDescending(c => c.MatchingScore)
            .ThenByDescending(c => c.CreatedAt)
            .ToListAsync();
    }

    public async Task<HireAgentConversation?> GetConversationByCandidateAndCampaignAsync(string candidateId, Guid campaignId)
    {
        return await _dbContext.HireAgentConversations.FirstOrDefaultAsync(c => c.CandidateId == candidateId && c.CampaignId == campaignId);
    }

    public async Task<HireAgentConversation?> GetActiveConversationByChatIdAsync(Guid chatConversationId)
    {
        return await _dbContext.HireAgentConversations.FirstOrDefaultAsync(c => c.ConversationId == chatConversationId && c.Status == "Screening");
    }

    public async Task CreateCampaignAsync(HireAgentCampaign campaign)
    {
        await _dbSet.AddAsync(campaign);
        await _dbContext.SaveChangesAsync();
    }

    public async Task UpdateCampaignAsync(HireAgentCampaign campaign)
    {
        _dbSet.Update(campaign);
        await _dbContext.SaveChangesAsync();
    }

    public async Task CreateConversationAsync(HireAgentConversation conversation)
    {
        await _dbContext.HireAgentConversations.AddAsync(conversation);
        await _dbContext.SaveChangesAsync();
    }

    public async Task UpdateConversationAsync(HireAgentConversation conversation)
    {
        _dbContext.HireAgentConversations.Update(conversation);
        await _dbContext.SaveChangesAsync();
    }

    public async Task<List<HireAgentConversation>> GetConversationsByCandidateAsync(string candidateId)
    {
        return await _dbContext.HireAgentConversations.Where(c => c.CandidateId == candidateId).ToListAsync();
    }
}

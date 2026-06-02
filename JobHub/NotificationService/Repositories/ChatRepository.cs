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

public class ChatRepository : GenericRepository<NotificationDbContext, Message>, IChatRepository
{
    private readonly NotificationDbContext _dbContext;

    public ChatRepository(NotificationDbContext dbContext) : base(dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<Conversation?> GetConversationAsync(Guid conversationId)
    {
        return await _dbContext.Conversations.FirstOrDefaultAsync(c => c.Id == conversationId && !c.IsDeleted);
    }

    public async Task<Conversation?> GetConversationByParticipantsAsync(string participantA, string participantB)
    {
        var pA = participantA.ToLower();
        var pB = participantB.ToLower();

        return await _dbContext.Conversations.FirstOrDefaultAsync(c =>
            ((c.ParticipantA.ToLower() == pA && c.ParticipantB.ToLower() == pB) ||
             (c.ParticipantA.ToLower() == pB && c.ParticipantB.ToLower() == pA)) && !c.IsDeleted);
    }

    public async Task<List<Conversation>> GetConversationsForUserAsync(string userId)
    {
        var uid = userId.ToLower();

        return await _dbContext.Conversations
            .Where(c => (c.ParticipantA.ToLower() == uid || c.ParticipantB.ToLower() == uid) && !c.IsDeleted)
            .OrderByDescending(c => c.LastMessageAt ?? c.CreatedAt)
            .ToListAsync();
    }

    public async Task<List<Message>> GetMessagesForConversationAsync(Guid conversationId, int limit, DateTimeOffset? before)
    {
        var query = _dbSet.Where(m => m.ConversationId == conversationId && !m.IsDeleted);

        if (before.HasValue)
        {
            query = query.Where(m => m.CreatedAt < before.Value);
        }

        // Đọc lịch sử sắp xếp từ mới nhất đến cũ nhất
        return await query.OrderByDescending(m => m.CreatedAt)
            .Take(limit)
            .ToListAsync();
    }

    public async Task<int> GetUnreadCountAsync(Guid conversationId, string userId)
    {
        var uid = userId.ToLower();

        return await _dbSet.CountAsync(m => m.ConversationId == conversationId &&
                                           m.SenderId.ToLower() != uid &&
                                           !m.IsRead && !m.IsDeleted);
    }

    public async Task MarkMessagesAsReadAsync(Guid conversationId, string userId)
    {
        var uid = userId.ToLower();

        var unreadMessages = await _dbSet.Where(m => m.ConversationId == conversationId &&
                                                   m.SenderId.ToLower() != uid &&
                                                   !m.IsRead && !m.IsDeleted)
                                         .ToListAsync();

        if (unreadMessages.Count > 0)
        {
            foreach (var msg in unreadMessages)
            {
                msg.IsRead = true;
            }
            await _dbContext.SaveChangesAsync();
        }
    }

    public async Task CreateConversationAsync(Conversation conversation)
    {
        await _dbContext.Conversations.AddAsync(conversation);
        await _dbContext.SaveChangesAsync();
    }

    public async Task UpdateConversationAsync(Conversation conversation)
    {
        _dbContext.Conversations.Update(conversation);
        await _dbContext.SaveChangesAsync();
    }
}

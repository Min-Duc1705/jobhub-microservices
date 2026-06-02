using CommonService.Repository;
using NotificationService.Models;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Repositories.Interface;

public interface IChatRepository : IGenericRepository<Message>
{
    Task<Conversation?> GetConversationAsync(Guid conversationId);
    Task<Conversation?> GetConversationByParticipantsAsync(string participantA, string participantB);
    Task<List<Conversation>> GetConversationsForUserAsync(string userId);
    Task<List<Message>> GetMessagesForConversationAsync(Guid conversationId, int limit, DateTimeOffset? before);
    Task<int> GetUnreadCountAsync(Guid conversationId, string userId);
    Task MarkMessagesAsReadAsync(Guid conversationId, string userId);
    Task CreateConversationAsync(Conversation conversation);
    Task UpdateConversationAsync(Conversation conversation);
}

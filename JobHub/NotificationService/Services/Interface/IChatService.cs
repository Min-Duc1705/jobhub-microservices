using NotificationService.Models.Response;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NotificationService.Services.Interface;

public interface IChatService
{
    Task<MessageResponse> SendMessageAsync(string senderId, string receiverId, string content, string type = "text");
    Task<List<ConversationResponse>> GetConversationsForUserAsync(string userId);
    Task<List<MessageResponse>> GetChatHistoryAsync(string userId, Guid conversationId, int limit = 50, DateTimeOffset? before = null);
    Task MarkAsReadAsync(string userId, Guid conversationId);
    Task<ConversationResponse> GetOrCreateConversationAsync(string participantA, string participantB);
}

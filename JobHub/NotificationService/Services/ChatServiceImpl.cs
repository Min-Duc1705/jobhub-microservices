using AutoMapper;
using CommonService.Exceptions;
using NotificationService.Models;
using NotificationService.Models.Response;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace NotificationService.Services;

public class ChatServiceImpl : IChatService
{
    private readonly IChatRepository _chatRepo;
    private readonly IMapper _mapper;

    public ChatServiceImpl(IChatRepository chatRepo, IMapper mapper)
    {
        _chatRepo = chatRepo;
        _mapper = mapper;
    }

    public async Task<ConversationResponse> GetOrCreateConversationAsync(string participantA, string participantB)
    {
        if (string.IsNullOrWhiteSpace(participantA) || string.IsNullOrWhiteSpace(participantB))
            throw new BadRequestException("ID người tham gia không được trống.");

        var conv = await _chatRepo.GetConversationByParticipantsAsync(participantA, participantB);
        if (conv == null)
        {
            conv = new Conversation
            {
                Id = Guid.NewGuid(),
                ParticipantA = participantA,
                ParticipantB = participantB,
                CreatedAt = DateTimeOffset.UtcNow
            };
            await _chatRepo.CreateConversationAsync(conv);
        }

        var res = _mapper.Map<ConversationResponse>(conv);
        res.UnreadCount = await _chatRepo.GetUnreadCountAsync(conv.Id, participantA); // ban đầu là 0 hoặc tính theo người gọi
        return res;
    }

    public async Task<MessageResponse> SendMessageAsync(string senderId, string receiverId, string content, string type = "text")
    {
        if (string.IsNullOrWhiteSpace(content))
            throw new BadRequestException("Nội dung tin nhắn không được trống.");

        // 1. Lấy hoặc tạo cuộc hội thoại
        var conv = await _chatRepo.GetConversationByParticipantsAsync(senderId, receiverId);
        if (conv == null)
        {
            conv = new Conversation
            {
                Id = Guid.NewGuid(),
                ParticipantA = senderId,
                ParticipantB = receiverId,
                CreatedAt = DateTimeOffset.UtcNow
            };
            await _chatRepo.CreateConversationAsync(conv);
        }

        // 2. Tạo tin nhắn mới
        var message = new Message
        {
            Id = Guid.NewGuid(),
            ConversationId = conv.Id,
            SenderId = senderId,
            Content = content,
            Type = type,
            IsRead = false,
            CreatedAt = DateTimeOffset.UtcNow
        };

        await _chatRepo.AddAsync(message);
        await _chatRepo.SaveChangesAsync();

        // 3. Cập nhật thông tin tin nhắn cuối của cuộc hội thoại
        conv.LastMessageContent = content;
        conv.LastMessageAt = message.CreatedAt;
        await _chatRepo.UpdateConversationAsync(conv);

        return _mapper.Map<MessageResponse>(message);
    }

    public async Task<List<ConversationResponse>> GetConversationsForUserAsync(string userId)
    {
        var list = await _chatRepo.GetConversationsForUserAsync(userId);
        var responses = new List<ConversationResponse>();

        foreach (var conv in list)
        {
            var res = _mapper.Map<ConversationResponse>(conv);
            res.UnreadCount = await _chatRepo.GetUnreadCountAsync(conv.Id, userId);
            responses.Add(res);
        }

        return responses;
    }

    public async Task<List<MessageResponse>> GetChatHistoryAsync(string userId, Guid conversationId, int limit = 50, DateTimeOffset? before = null)
    {
        var conv = await _chatRepo.GetConversationAsync(conversationId);
        if (conv == null)
            throw new NotFoundException("Không tìm thấy cuộc hội thoại.");

        var uid = userId.ToLower();
        if (conv.ParticipantA.ToLower() != uid && conv.ParticipantB.ToLower() != uid)
            throw new BadRequestException("Bạn không có quyền xem cuộc hội thoại này.");

        var messages = await _chatRepo.GetMessagesForConversationAsync(conversationId, limit, before);
        
        // Sắp xếp lại lịch sử theo thứ tự thời gian tăng dần trước khi trả về Client
        var orderedMessages = messages.OrderBy(m => m.CreatedAt).ToList();

        return _mapper.Map<List<MessageResponse>>(orderedMessages);
    }

    public async Task MarkAsReadAsync(string userId, Guid conversationId)
    {
        var conv = await _chatRepo.GetConversationAsync(conversationId);
        if (conv == null)
            throw new NotFoundException("Không tìm thấy cuộc hội thoại.");

        var uid = userId.ToLower();
        if (conv.ParticipantA.ToLower() != uid && conv.ParticipantB.ToLower() != uid)
            throw new BadRequestException("Bạn không có quyền cập nhật cuộc hội thoại này.");

        await _chatRepo.MarkMessagesAsReadAsync(conversationId, userId);
    }
}

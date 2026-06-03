using AutoMapper;
using CommonService.Exceptions;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.DependencyInjection;
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
    private readonly IServiceScopeFactory _scopeFactory;

    public ChatServiceImpl(IChatRepository chatRepo, IMapper mapper, IServiceScopeFactory scopeFactory)
    {
        _chatRepo = chatRepo;
        _mapper = mapper;
        _scopeFactory = scopeFactory;
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

        // 4. Nếu đây là cuộc trò chuyện sàng lọc đang kích hoạt của HireAgent, kích hoạt AI xử lý trả lời không đồng bộ
        _ = Task.Run(async () =>
        {
            try
            {
                using (var scope = _scopeFactory.CreateScope())
                {
                    var hireAgentRepo = scope.ServiceProvider.GetRequiredService<IHireAgentRepository>();
                    var hireAgentService = scope.ServiceProvider.GetRequiredService<IHireAgentService>();
                    var chatService = scope.ServiceProvider.GetRequiredService<IChatService>();
                    var hubContext = scope.ServiceProvider.GetRequiredService<IHubContext<NotificationService.Hubs.ChatHub>>();
                    var config = scope.ServiceProvider.GetRequiredService<Microsoft.Extensions.Configuration.IConfiguration>();

                    // Kiểm tra yêu cầu đổi lịch / hủy phỏng vấn
                    var lowerContent = content.ToLower().Trim();
                    bool isRescheduleRequest = lowerContent.Contains("đổi lịch") || 
                                               lowerContent.Contains("hẹn lại") || 
                                               lowerContent.Contains("đổi giờ") || 
                                               lowerContent.Contains("chuyển lịch") || 
                                               lowerContent.Contains("reschedule");

                    bool isCancelRequest = lowerContent.Contains("không nhận job") || 
                                           lowerContent.Contains("không phỏng vấn") || 
                                           lowerContent.Contains("hủy phỏng vấn") || 
                                           lowerContent.Contains("hủy lịch") || 
                                           lowerContent.Contains("hủy hẹn") || 
                                           lowerContent.Contains("không tham gia") || 
                                           lowerContent.Contains("từ chối") || 
                                           lowerContent.Contains("rút hồ sơ") || 
                                           (lowerContent.Contains("đổi ý") && (lowerContent.Contains("không") || lowerContent.Contains("hủy")));

                    if (isRescheduleRequest || isCancelRequest)
                    {
                        var candidateConversations = await hireAgentRepo.GetConversationsByCandidateAsync(senderId);
                        var targetConv = candidateConversations
                            .Where(c => c.ConversationId == conv.Id)
                            .OrderByDescending(c => c.CreatedAt)
                            .FirstOrDefault();

                        if (targetConv != null && (targetConv.Status == "Scheduled" || targetConv.Status == "Passed" || targetConv.Status == "Screening"))
                        {
                            var campaign = await hireAgentRepo.GetCampaignAsync(targetConv.CampaignId);
                            if (campaign != null)
                            {
                                if (isCancelRequest)
                                {
                                    // Chuyển trạng thái sang Failed (Không đạt)
                                    targetConv.Status = "Failed";
                                    targetConv.InterviewDate = null;
                                    await hireAgentRepo.UpdateConversationAsync(targetConv);

                                    var cancelMsg = "[HỆ THỐNG] Đã ghi nhận yêu cầu hủy phỏng vấn và rút hồ sơ của bạn cho vị trí này. Trạng thái ứng tuyển đã chuyển sang Không đạt. Cảm ơn bạn và chúc bạn may mắn!";
                                    var sysMsgResponse = await chatService.SendMessageAsync(campaign.RecruiterId, targetConv.CandidateId, cancelMsg, "text");
                                    await hubContext.Clients.Group(targetConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);
                                    await hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);

                                    // Gửi thông báo AI đã rời cuộc trò chuyện
                                    var leaveMsg = "[HỆ THỐNG] Trợ lý AI đã rời khỏi cuộc trò chuyện.";
                                    var leaveMsgResponse = await chatService.SendMessageAsync(campaign.RecruiterId, targetConv.CandidateId, leaveMsg, "text");
                                    await hubContext.Clients.Group(targetConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                                    await hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                                    
                                    return; // Kết thúc sớm
                                }
                                else if (isRescheduleRequest && (targetConv.Status == "Scheduled" || targetConv.Status == "Passed"))
                                {
                                    // Reset trạng thái về Passed để có thể đặt lịch lại
                                    targetConv.Status = "Passed";
                                    targetConv.InterviewDate = null;
                                    await hireAgentRepo.UpdateConversationAsync(targetConv);

                                    var frontendUrl = config["FrontendUrl"] ?? "http://localhost:5173";
                                    var scheduleMsg = $"[HỆ THỐNG] Nhận được yêu cầu đổi lịch phỏng vấn. Bạn vui lòng chọn lại thời gian phỏng vấn mới tại đây: {frontendUrl.TrimEnd('/')}/schedule/{campaign.Id}";
                                    
                                    var sysMsgResponse = await chatService.SendMessageAsync(campaign.RecruiterId, targetConv.CandidateId, scheduleMsg, "text");
                                    await hubContext.Clients.Group(targetConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);
                                    await hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);
                                    return; // Kết thúc sớm
                                }
                            }
                        }
                    }

                    var agentConv = await hireAgentRepo.GetActiveConversationByChatIdAsync(conv.Id);
                    if (agentConv != null && senderId.ToLower() == agentConv.CandidateId.ToLower())
                    {
                        await hireAgentService.ProcessCandidateReplyAsync(conv.Id, content);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgent-Intercept] Lỗi xử lý chặn tin nhắn: {ex.Message}");
            }
        });

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

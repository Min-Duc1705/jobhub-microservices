using AutoMapper;
using CommonService.Exceptions;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Models.Response;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace NotificationService.Services;

public class ChatServiceImpl : IChatService
{
    private readonly IChatRepository _chatRepo;
    private readonly IMapper _mapper;
    private readonly IServiceScopeFactory _scopeFactory;
    private static readonly HttpClient _httpClient = new HttpClient();

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

        // 5. Nếu receiverId là ai_assistant, gọi AI Assistant xử lý trả lời không đồng bộ (chỉ áp dụng cho Telegram)
        if (receiverId.Equals("ai_assistant", StringComparison.OrdinalIgnoreCase) && 
            !senderId.Equals("ai_assistant", StringComparison.OrdinalIgnoreCase) && 
            type == "telegram")
        {
            _ = Task.Run(async () =>
            {
                try
                {
                    using (var scope = _scopeFactory.CreateScope())
                    {
                        var chatService = scope.ServiceProvider.GetRequiredService<IChatService>();
                        var hubContext = scope.ServiceProvider.GetRequiredService<IHubContext<NotificationService.Hubs.ChatHub>>();
                        var config = scope.ServiceProvider.GetRequiredService<Microsoft.Extensions.Configuration.IConfiguration>();
                        var dbContext = scope.ServiceProvider.GetRequiredService<NotificationDbContext>();
                        var telegramBotService = scope.ServiceProvider.GetRequiredService<ITelegramBotService>();

                        // a. Lấy profile từ AuthService
                        var secretKey = config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
                        var issuer = config["Jwt:Issuer"] ?? "JobHub";
                        var audience = config["Jwt:Audience"] ?? "JobHubClient";
                        var adminToken = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

                        string email = "user@jobhub.com";
                        string role = "USER";
                        string username = "Người dùng";

                        try
                        {
                            var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{senderId}");
                            userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", adminToken);
                            var userRes = await _httpClient.SendAsync(userReq);

                            if (userRes.IsSuccessStatusCode)
                            {
                                var userContent = await userRes.Content.ReadAsStringAsync();
                                using var userJson = JsonDocument.Parse(userContent);
                                var data = userJson.RootElement.GetProperty("data");
                                email = data.GetProperty("email").GetString() ?? email;
                                username = data.GetProperty("username").GetString() ?? username;
                                if (data.TryGetProperty("role", out var roleProp) && roleProp.ValueKind != JsonValueKind.Null)
                                {
                                    role = roleProp.GetProperty("name").GetString() ?? role;
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"[ChatServiceImpl-AI] Lỗi lấy profile từ AuthService: {ex.Message}");
                        }

                        // b. Tạo token đại diện cho User
                        var userToken = InternalTokenGenerator.GenerateTokenForUser(secretKey, issuer, audience, Guid.Parse(senderId), email, role, username);

                        // c. Lấy lịch sử hội thoại thực tế từ DB (lọc bỏ tin nhắn hiện tại vừa gửi)
                        var dbMessages = await dbContext.Messages
                            .Where(m => m.ConversationId == conv.Id && m.Id != message.Id)
                            .OrderByDescending(m => m.CreatedAt)
                            .Take(15)
                            .ToListAsync();

                        dbMessages.Reverse();

                        var history = dbMessages.Select(m => new
                        {
                            role = m.SenderId.Equals(senderId, StringComparison.OrdinalIgnoreCase) ? "user" : "model",
                            content = m.Content
                        }).ToList();

                        // d. Build request gửi lên CVIntelligenceService
                        var aiRequestPayload = new
                        {
                            message = content,
                            image_base64 = (string?)null,
                            file_content = (string?)null,
                            conversation_history = history
                        };

                        var xSessionId = $"session_{senderId}";

                        var aiReq = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/assistant/chat");
                        aiReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", userToken);
                        aiReq.Headers.Add("X-Session-Id", xSessionId);
                        aiReq.Content = new StringContent(JsonSerializer.Serialize(aiRequestPayload), Encoding.UTF8, "application/json");

                        var aiRes = await _httpClient.SendAsync(aiReq);
                        string aiReply = "Xin lỗi, đã xảy ra lỗi kết nối với AI Assistant. Vui lòng thử lại sau.";

                        if (aiRes.IsSuccessStatusCode)
                        {
                            var aiContent = await aiRes.Content.ReadAsStringAsync();
                            using var aiJson = JsonDocument.Parse(aiContent);
                            aiReply = aiJson.RootElement.GetProperty("reply").GetString() ?? aiReply;

                            if (type == "telegram" && aiJson.RootElement.TryGetProperty("actions_taken", out var actionsProp) && actionsProp.ValueKind == JsonValueKind.Array)
                            {
                                foreach (var action in actionsProp.EnumerateArray())
                                {
                                    if (action.TryGetProperty("action_type", out var actTypeProp) && actTypeProp.GetString() == "tool_navigate_to_page")
                                    {
                                        if (action.TryGetProperty("data", out var dataProp) && dataProp.TryGetProperty("path", out var pathProp))
                                        {
                                            var path = pathProp.GetString();
                                            if (!string.IsNullOrEmpty(path))
                                            {
                                                var frontendUrl = config["FrontendUrl"] ?? "https://jobhub-frontend-two.vercel.app";
                                                var absoluteUrl = path.StartsWith("http") ? path : $"{frontendUrl.TrimEnd('/')}/{path.TrimStart('/')}";
                                                aiReply += $"\n\n👉 [Click vào đây để mở trang]({absoluteUrl})";
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // e. Lưu tin nhắn trả lời của AI vào DB (sử dụng loại "telegram" nếu tin nhắn gốc gửi từ telegram)
                        var replyType = type == "telegram" ? "telegram" : "text";
                        var aiMsgResponse = await chatService.SendMessageAsync("ai_assistant", senderId, aiReply, replyType);

                        // f. Phát SignalR real-time cho User
                        await hubContext.Clients.Group(senderId.ToLower()).SendAsync("ReceiveMessage", aiMsgResponse);

                        // g. Nếu nguồn từ Telegram, gửi tin nhắn đến Telegram của User
                        if (type == "telegram")
                        {
                            await telegramBotService.SendTextMessageAsync(Guid.Parse(senderId), aiReply);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[ChatServiceImpl-AI] Lỗi xử lý AI Assistant: {ex.Message}");
                }
            });
        }

        // 6. Nếu receiverId không phải là ai_assistant, gửi thông báo đẩy đến Telegram của receiver (nếu họ có liên kết)
        if (!receiverId.Equals("ai_assistant", StringComparison.OrdinalIgnoreCase) && 
            !senderId.Equals("ai_assistant", StringComparison.OrdinalIgnoreCase))
        {
            _ = Task.Run(async () =>
            {
                try
                {
                    using (var scope = _scopeFactory.CreateScope())
                    {
                        var config = scope.ServiceProvider.GetRequiredService<Microsoft.Extensions.Configuration.IConfiguration>();
                        var telegramBotService = scope.ServiceProvider.GetRequiredService<ITelegramBotService>();
                        
                        // Lấy tên người gửi
                        var secretKey = config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
                        var issuer = config["Jwt:Issuer"] ?? "JobHub";
                        var audience = config["Jwt:Audience"] ?? "JobHubClient";
                        var adminToken = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);
                        
                        string senderName = "Người dùng";
                        try
                        {
                            var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{senderId}");
                            userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", adminToken);
                            var userRes = await _httpClient.SendAsync(userReq);

                            if (userRes.IsSuccessStatusCode)
                            {
                                var userContent = await userRes.Content.ReadAsStringAsync();
                                using var userJson = JsonDocument.Parse(userContent);
                                var data = userJson.RootElement.GetProperty("data");
                                senderName = data.GetProperty("username").GetString() ?? senderName;
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"[ChatServiceImpl-Notification] Lỗi lấy profile người gửi: {ex.Message}");
                        }

                        // Gửi thông báo qua Telegram cho người nhận
                        if (Guid.TryParse(receiverId, out Guid receiverGuid))
                        {
                            var frontendUrl = config["FrontendUrl"] ?? "https://jobhub-frontend-two.vercel.app";
                            var title = $"💬 Tin nhắn mới từ {senderName}";
                            var messageText = $"{content}\n\n👉 [Mở Chat để trả lời]({frontendUrl.TrimEnd('/')}/chat)\n✍️ Trả lời (Reply) tin nhắn này để chat trực tiếp\n\nRef: {senderId}";
                            await telegramBotService.SendPushNotificationAsync(receiverGuid, title, messageText);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[ChatServiceImpl-Notification] Lỗi gửi thông báo chat Telegram: {ex.Message}");
                }
            });
        }

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

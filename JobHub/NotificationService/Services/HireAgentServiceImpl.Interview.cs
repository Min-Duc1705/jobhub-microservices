using CommonService.Exceptions;
using Microsoft.AspNetCore.SignalR;
using NotificationService.Hubs;
using NotificationService.Models;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Helpers;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace NotificationService.Services;

// Partial class — phần xử lý phỏng vấn: screening chat + đặt lịch + xác nhận lịch
public partial class HireAgentServiceImpl
{
    // ─── Keywords để detect candidate xác nhận/đổi lịch qua chat ─────────────
    private static readonly string[] _confirmKeywords =
        { "đồng ý", "ok", "xác nhận", "chốt", "được", "nhất trí", "oke", "okie", "accept", "confirm", "✅" };
    private static readonly string[] _rescheduleKeywords =
        { "đổi lịch", "thay đổi", "dời lịch", "không được", "bận", "reschedule", "change", "hủy", "cancel" };

    // ─── ProcessCandidateReplyAsync: xử lý tin nhắn candidate gửi lên ────────
    public async Task ProcessCandidateReplyAsync(Guid chatConversationId, string candidateMessage)
    {
        try
        {
            var agentConv = await _hireAgentRepo.GetActiveConversationByChatIdAsync(chatConversationId);
            if (agentConv == null) return;

            var campaign = await _hireAgentRepo.GetCampaignAsync(agentConv.CampaignId);
            if (campaign == null) return;

            // ── Intercept: candidate đang ở trạng thái PendingCandidateConfirm ──
            if (agentConv.Status == "PendingCandidateConfirm")
            {
                var msgLower = candidateMessage.ToLowerInvariant().Trim();

                if (campaign.InterviewDate.HasValue && campaign.BackupInterviewDate.HasValue)
                {
                    // 1. Check if candidate chose Option 1
                    if (msgLower == "1" || msgLower.Contains("phương án 1") || msgLower.Contains("phuong an 1") || 
                        msgLower.Contains("lịch 1") || msgLower.Contains("lich 1") || msgLower.Contains("option 1") || 
                        msgLower.Contains("pa 1") || msgLower.Contains("pa1") || msgLower.Contains("chọn 1") || msgLower.Contains("chon 1"))
                    {
                        agentConv.InterviewDate = campaign.InterviewDate;
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);
                        await ConfirmInterviewAsync(agentConv.CampaignId, agentConv.CandidateId);
                        return;
                    }

                    // 2. Check if candidate chose Option 2
                    if (msgLower == "2" || msgLower.Contains("phương án 2") || msgLower.Contains("phuong an 2") || 
                        msgLower.Contains("lịch 2") || msgLower.Contains("lich 2") || msgLower.Contains("option 2") || 
                        msgLower.Contains("pa 2") || msgLower.Contains("pa2") || msgLower.Contains("chọn 2") || msgLower.Contains("chon 2"))
                    {
                        agentConv.InterviewDate = campaign.BackupInterviewDate;
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);
                        await ConfirmInterviewAsync(agentConv.CampaignId, agentConv.CandidateId);
                        return;
                    }

                    // 3. Check if candidate chose Option 3 / Busy with both / Reschedule
                    if (msgLower == "3" || msgLower.Contains("bận cả hai") || msgLower.Contains("ban ca hai") || 
                        msgLower.Contains("bận cả 2") || msgLower.Contains("ban ca 2") || msgLower.Contains("không được cả hai") || 
                        _rescheduleKeywords.Any(k => msgLower.Contains(k)))
                    {
                        await ProposeRescheduleAsync(agentConv.CampaignId, agentConv.CandidateId, candidateMessage);
                        return;
                    }

                    // 4. Default fallback: prompt them to choose clearly
                    var date1Str = campaign.InterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm");
                    var date2Str = campaign.BackupInterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm");

                    var reminderMsg = $"[HỆ THỐNG] Bạn vui lòng chọn rõ phương án lịch phỏng vấn:\n" +
                                      $"• Nhắn **1** để chọn Phương án 1: **{date1Str}**\n" +
                                      $"• Nhắn **2** để chọn Phương án 2: **{date2Str}**\n" +
                                      $"• Nhắn **3** hoặc \"Bận cả hai\" nếu bạn muốn đề xuất khung giờ khác.";
                    var reminderResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, reminderMsg, "text");
                    await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", reminderResponse);
                    await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", reminderResponse);
                    return;
                }
                else
                {
                    // Fallback for legacy campaigns without preset dates
                    if (_confirmKeywords.Any(k => msgLower.Contains(k)))
                    {
                        await ConfirmInterviewAsync(agentConv.CampaignId, agentConv.CandidateId);
                        return;
                    }

                    if (_rescheduleKeywords.Any(k => msgLower.Contains(k)))
                    {
                        await ProposeRescheduleAsync(agentConv.CampaignId, agentConv.CandidateId, candidateMessage);
                        return;
                    }

                    var reminderMsg = $"[HỆ THỐNG] Bạn vui lòng trả lời rõ ràng hơn:\n" +
                                      $"• Nhắn \"✅ Đồng ý\" để xác nhận lịch phỏng vấn.\n" +
                                      $"• Nhắn \"🔄 Đổi lịch\" để đề xuất thời gian khác.";
                    var reminderResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, reminderMsg, "text");
                    await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", reminderResponse);
                    await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", reminderResponse);
                    return;
                }
            }

            // ── Luồng bình thường: AI phỏng vấn sàng lọc ────────────────────
            if (agentConv.Status != "Screening") return;

            // 1. Lấy lịch sử chat (15 tin gần nhất)
            var messages   = await _chatRepo.GetMessagesForConversationAsync(chatConversationId, 15, null);
            var sessionStartTime = agentConv.CreatedAt.AddMinutes(-1);
            var chatHistory = messages
                .Where(m => m.CreatedAt >= sessionStartTime)
                .OrderBy(m => m.CreatedAt)
                .Select(msg => (object)new
                {
                    sender  = msg.SenderId.Equals(agentConv.CandidateId, StringComparison.OrdinalIgnoreCase) ? "candidate" : "agent",
                    content = msg.Content
                }).ToList();

            var recruiterMeta = await UserInfoHelper.GetRecruiterAndCompanyDetailsAsync(campaign.RecruiterId, _config);
            var frontendUrl   = _config["FrontendUrl"] ?? "http://localhost:5173";
            var jobUrl        = $"{frontendUrl.TrimEnd('/')}/jobs/{campaign.JobId}";

            // 2. Gọi CVIntelligenceService để nhận câu trả lời tiếp theo
            var payload = new
            {
                job_description = campaign.JobDescription,
                cv_text         = agentConv.CvText,
                chat_history    = chatHistory,
                recruiter_name  = recruiterMeta.RecruiterName,
                company_name    = recruiterMeta.CompanyName,
                job_name        = campaign.JobName,
                job_url         = jobUrl
            };

            var request = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/cv/hire-agent/chat");
            request.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

            var response = await _httpClient.SendAsync(request);
            if (!response.IsSuccessStatusCode) return;

            var jsonDoc     = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
            var reply       = jsonDoc.RootElement.GetProperty("reply").GetString() ?? "";
            bool isCompleted = jsonDoc.RootElement.GetProperty("is_completed").GetBoolean();
            bool isPassed    = jsonDoc.RootElement.GetProperty("is_passed").GetBoolean();

            // 3. Gửi tin nhắn trả lời của Agent
            var chatMessageResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, reply, "text");
            await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);

            // 4. Xử lý kết quả phỏng vấn
            if (isCompleted)
            {
                if (isPassed)
                {
                    if (campaign.InterviewDate.HasValue && campaign.BackupInterviewDate.HasValue)
                    {
                        agentConv.Status = "PendingCandidateConfirm";
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);

                        var date1Str = campaign.InterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm");
                        var date2Str = campaign.BackupInterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm");

                        var proposalMsg = $"[HỆ THỐNG] 🎉 Xin chúc mừng! Bạn đã xuất sắc vượt qua vòng phỏng vấn sàng lọc sơ bộ cho vị trí **{campaign.JobName}**!\n\n" +
                                          $"Nhà tuyển dụng đề xuất lịch phỏng vấn chính thức với 2 phương án thời gian:\n" +
                                          $"1️⃣ Phương án 1: **{date1Str}**\n" +
                                          $"2️⃣ Phương án 2: **{date2Str}**\n\n" +
                                          $"Vui lòng trả lời bằng cách nhắn số **1** hoặc **2** để xác nhận lịch phỏng vấn phù hợp với bạn.\n" +
                                          $"Nếu bạn bận cả hai, vui lòng nhắn **\"Bận cả hai\"** (hoặc số **3**) để Nhà tuyển dụng chọn ngày khác.";

                        var passedResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, proposalMsg, "text");
                        await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", passedResponse);
                        await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", passedResponse);

                        var chatPageUrl = $"{frontendUrl.TrimEnd('/')}/chat";
                        _ = SendProposalEmailAsync(campaign, agentConv.CandidateId, $"{date1Str} hoặc {date2Str}", chatPageUrl);

                        // Gửi thông báo hệ thống và đẩy qua Telegram/SignalR cho HR
                        _ = Task.Run(async () =>
                        {
                            try
                            {
                                var candidateInfo = await UserInfoHelper.GetUserDetailsAsync(agentConv.CandidateId, _config);
                                var candidateName = candidateInfo.FullName ?? "Ứng viên";
                                var notifTitle = "🎉 Ứng viên vượt qua sàng lọc AI";
                                var notifBody = $"Ứng viên {candidateName} đã vượt qua vòng sàng lọc sơ bộ cho vị trí \"{campaign.JobName}\". Hệ thống đang tự động gửi đề xuất hẹn lịch phỏng vấn.";
                                SendNotificationToHr(campaign.RecruiterId, campaign.Id, agentConv.CandidateId, notifTitle, notifBody, $"hire_agent_passed:{campaign.Id}:{agentConv.CandidateId}");
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"[HireAgent-NotifyHR] Lỗi khi gửi thông báo cho HR: {ex.Message}");
                            }
                        });
                    }
                    else
                    {
                        agentConv.Status = "Passed";
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);

                        var passedMsg = "[HỆ THỐNG] 🎉 Xin chúc mừng! Bạn đã xuất sắc vượt qua vòng sàng lọc sơ bộ! " +
                                       "Nhà tuyển dụng sẽ liên hệ để sắp xếp lịch phỏng vấn cho bạn sớm nhất có thể. " +
                                       "Hãy chờ thông báo qua email hoặc khung chat này!";
                        var passedResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, passedMsg, "text");
                        await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", passedResponse);
                        await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", passedResponse);

                        // Gửi thông báo hệ thống và đẩy qua Telegram/SignalR cho HR
                        _ = Task.Run(async () =>
                        {
                            try
                            {
                                var candidateInfo = await UserInfoHelper.GetUserDetailsAsync(agentConv.CandidateId, _config);
                                var candidateName = candidateInfo.FullName ?? "Ứng viên";
                                var notifTitle = "🎉 Ứng viên vượt qua sàng lọc AI";
                                var notifBody = $"Ứng viên {candidateName} đã xuất sắc vượt qua vòng phỏng vấn sàng lọc sơ bộ cho vị trí \"{campaign.JobName}\". Vui lòng xếp lịch phỏng vấn chính thức.";
                                SendNotificationToHr(campaign.RecruiterId, campaign.Id, agentConv.CandidateId, notifTitle, notifBody, $"hire_agent_passed:{campaign.Id}:{agentConv.CandidateId}");
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"[HireAgent-NotifyHR] Lỗi khi gửi thông báo cho HR: {ex.Message}");
                            }
                        });
                    }
                }
                else
                {
                    agentConv.Status = "Failed";
                    await _hireAgentRepo.UpdateConversationAsync(agentConv);

                    var leaveMsg = "[HỆ THỐNG] Trợ lý AI đã kết thúc buổi đánh giá và rời khỏi cuộc trò chuyện.";
                    var leaveResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, leaveMsg, "text");
                    await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", leaveResponse);
                    await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", leaveResponse);
                }
            }
            else
            {
                agentConv.LastQuestionAt = DateTimeOffset.UtcNow;
                await _hireAgentRepo.UpdateConversationAsync(agentConv);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[HireAgent] Lỗi khi xử lý câu trả lời của ứng viên: {ex.Message}");
        }
    }

    // ─── ScheduleInterviewAsync: HR đặt lịch đề xuất ────────────────────────
    public async Task<HireAgentConversation> ScheduleInterviewAsync(
        Guid campaignId, string candidateId, DateTimeOffset interviewDate)
    {
        var conversation = await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId)
            ?? throw new NotFoundException("Không tìm thấy hội thoại tuyển dụng AI của ứng viên.");

        conversation.Status        = "PendingCandidateConfirm";
        conversation.InterviewDate = interviewDate;
        await _hireAgentRepo.UpdateConversationAsync(conversation);

        var campaign = await _hireAgentRepo.GetCampaignAsync(campaignId);
        if (campaign != null)
        {
            var dateStr        = interviewDate.ToLocalTime().ToString("dd/MM/yyyy HH:mm");
            var frontendUrl    = _config["FrontendUrl"] ?? "http://localhost:5173";
            var chatPageUrl     = $"{frontendUrl.TrimEnd('/')}/chat";
 
            var proposalMsg = $"[HỆ THỐNG] 📋 Nhà tuyển dụng đề xuất lịch phỏng vấn cho vị trí **{campaign.JobName}** vào lúc **{dateStr}**.\n\n" +
                              $"Bạn có thể nhắn \"✅ Đồng ý\" ngay tại đây để xác nhận đồng ý lịch phỏng vấn này.";
            var msgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, candidateId, proposalMsg, "text");
            await _hubContext.Clients.Group(candidateId.ToLower()).SendAsync("ReceiveMessage", msgResponse);
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", msgResponse);
 
            _ = SendProposalEmailAsync(campaign, candidateId, dateStr, chatPageUrl);
        }

        return conversation;
    }

    // ─── ConfirmInterviewAsync: candidate xác nhận lịch ─────────────────────
    public async Task<HireAgentConversation> ConfirmInterviewAsync(Guid campaignId, string candidateId)
    {
        var conversation = await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId)
            ?? throw new NotFoundException("Không tìm thấy hội thoại tuyển dụng AI của ứng viên.");

        if (conversation.Status != "PendingCandidateConfirm")
            throw new BadRequestException("Hội thoại không ở trạng thái chờ xác nhận.");

        conversation.Status = "Scheduled";
        await _hireAgentRepo.UpdateConversationAsync(conversation);

        var campaign = await _hireAgentRepo.GetCampaignAsync(campaignId);
        if (campaign != null && conversation.InterviewDate.HasValue)
        {
            var interviewDate = conversation.InterviewDate.Value;
            var dateStr       = interviewDate.ToLocalTime().ToString("dd/MM/yyyy HH:mm");

            var confirmMsg = $"[HỆ THỐNG] ✅ Lịch phỏng vấn đã được chốt chính thức vào lúc **{dateStr}**! " +
                             $"Email xác nhận sẽ được gửi đến cả hai bên.";
            var msgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, candidateId, confirmMsg, "text");
            await _hubContext.Clients.Group(candidateId.ToLower()).SendAsync("ReceiveMessage", msgResponse);
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", msgResponse);

            _ = SendConfirmationEmailAsync(campaign, candidateId, interviewDate);

            // Gửi thông báo đẩy cho HR
            _ = Task.Run(async () =>
            {
                try
                {
                    var candidateInfo = await UserInfoHelper.GetUserDetailsAsync(candidateId, _config);
                    var candidateName = candidateInfo.FullName ?? "Ứng viên";
                    var notifTitle = "📅 Lịch phỏng vấn được xác nhận";
                    var notifBody = $"Ứng viên {candidateName} đã xác nhận lịch phỏng vấn cho vị trí \"{campaign.JobName}\" vào lúc {dateStr}.";
                    SendNotificationToHr(campaign.RecruiterId, campaignId, candidateId, notifTitle, notifBody, $"hire_agent_scheduled:{campaignId}:{candidateId}");
                }
                catch {}
            });
        }

        return conversation;
    }

    // ─── ProposeRescheduleAsync: candidate đề xuất đổi lịch ─────────────────
    public async Task<HireAgentConversation> ProposeRescheduleAsync(
        Guid campaignId, string candidateId, string? message = null)
    {
        var conversation = await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId)
            ?? throw new NotFoundException("Không tìm thấy hội thoại tuyển dụng AI của ứng viên.");

        // Reset về Passed — HR có thể chọn lịch mới, không giới hạn số lần
        conversation.Status        = "Passed";
        conversation.InterviewDate = null;
        await _hireAgentRepo.UpdateConversationAsync(conversation);

        var campaign = await _hireAgentRepo.GetCampaignAsync(campaignId);
        if (campaign != null)
        {
            var note = string.IsNullOrEmpty(message) ? "" : $"\nLý do từ ứng viên: \"{message}\"";
            var rescheduleMsg = $"[HỆ THỐNG] 🔄 Ứng viên đề xuất đổi lịch phỏng vấn.{note}\n" +
                                "Vui lòng vào trang quản lý chiến dịch để chọn lại ngày phỏng vấn.";
            var msgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, candidateId, rescheduleMsg, "text");
            await _hubContext.Clients.Group(candidateId.ToLower()).SendAsync("ReceiveMessage", msgResponse);
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", msgResponse);

            // Gửi thông báo đẩy cho HR
            _ = Task.Run(async () =>
            {
                try
                {
                    var candidateInfo = await UserInfoHelper.GetUserDetailsAsync(candidateId, _config);
                    var candidateName = candidateInfo.FullName ?? "Ứng viên";
                    var notifTitle = "🔄 Yêu cầu đổi lịch phỏng vấn";
                    var notifBody = $"Ứng viên {candidateName} báo bận cả hai khung giờ đề xuất cho vị trí \"{campaign.JobName}\". Vui lòng xếp lịch phỏng vấn khác.";
                    SendNotificationToHr(campaign.RecruiterId, campaignId, candidateId, notifTitle, notifBody, $"hire_agent_reschedule:{campaignId}:{candidateId}");
                }
                catch {}
            });
        }

        return conversation;
    }

    // ─── Private email helpers (fire-and-forget) ─────────────────────────────

    private Task SendProposalEmailAsync(HireAgentCampaign campaign, string candidateId, string dateStr, string schedulePageUrl)
        => Task.Run(async () =>
        {
            try
            {
                using var scope       = _scopeFactory.CreateScope();
                var emailSvc          = scope.ServiceProvider.GetRequiredService<IEmailService>();
                var candidateInfo     = await UserInfoHelper.GetUserDetailsAsync(candidateId, _config);
                var recruiterMeta     = await UserInfoHelper.GetRecruiterAndCompanyDetailsAsync(campaign.RecruiterId, _config);
                var recruiterDisplay  = $"Trợ lý AI đại diện cho {recruiterMeta.RecruiterName ?? "Nhà tuyển dụng"} thuộc {recruiterMeta.CompanyName ?? "đối tác JobHub"}";

                if (candidateInfo.Email != null)
                    await emailSvc.SendInterviewProposalEmailAsync(
                        candidateInfo.Email, candidateInfo.FullName ?? "Ứng viên",
                        campaign.JobName, dateStr, recruiterDisplay, schedulePageUrl);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgent-Email] Lỗi gửi email đề xuất lịch: {ex.Message}");
            }
        });

    private Task SendConfirmationEmailAsync(HireAgentCampaign campaign, string candidateId, DateTimeOffset interviewDate)
        => Task.Run(async () =>
        {
            try
            {
                using var scope      = _scopeFactory.CreateScope();
                var emailSvc         = scope.ServiceProvider.GetRequiredService<IEmailService>();
                var candidateInfo    = await UserInfoHelper.GetUserDetailsAsync(candidateId, _config);
                var recruiterMeta    = await UserInfoHelper.GetRecruiterAndCompanyDetailsAsync(campaign.RecruiterId, _config);
                var dateStr          = interviewDate.ToLocalTime().ToString("dd/MM/yyyy HH:mm");
                var frontendUrl      = _config["FrontendUrl"] ?? "http://localhost:5173";
                var recruiterDisplay = $"Trợ lý AI đại diện cho {recruiterMeta.RecruiterName ?? "Nhà tuyển dụng"} thuộc {recruiterMeta.CompanyName ?? "đối tác JobHub"}";

                if (candidateInfo.Email != null)
                    await emailSvc.SendInterviewEmailAsync(
                        candidateInfo.Email, candidateInfo.FullName ?? "Ứng viên",
                        campaign.JobName, dateStr, recruiterDisplay, $"{frontendUrl.TrimEnd('/')}/chat");

                if (recruiterMeta.Email != null)
                    await emailSvc.SendInterviewEmailToRecruiterAsync(
                        recruiterMeta.Email, candidateInfo.FullName ?? "Ứng viên",
                        campaign.JobName, dateStr, recruiterMeta.RecruiterName ?? "Nhà tuyển dụng",
                        $"{frontendUrl.TrimEnd('/')}/admin/hire-agent");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgent-Email] Lỗi gửi email xác nhận chính thức: {ex.Message}");
            }
        });

    // Helper gửi thông báo hệ thống và Telegram cho HR
    private void SendNotificationToHr(string recruiterId, Guid campaignId, string candidateId, string title, string message, string type)
    {
        _ = Task.Run(async () =>
        {
            try
            {
                using var scope = _scopeFactory.CreateScope();
                var notifSvc = scope.ServiceProvider.GetRequiredService<INotificationService>();
                var hubNotifContext = scope.ServiceProvider.GetRequiredService<IHubContext<NotificationHub>>();
                var telegramBotSvc = scope.ServiceProvider.GetRequiredService<ITelegramBotService>();

                if (Guid.TryParse(recruiterId, out var recruiterGuid))
                {
                    var notification = await notifSvc.CreateNotificationAsync(recruiterGuid, title, message, type);
                    var payload = new
                    {
                        id = notification.Id.ToString(),
                        title = notification.Title,
                        message = notification.Message,
                        isRead = notification.IsRead,
                        createdDate = notification.CreatedDate,
                        type = notification.Type
                    };

                    await hubNotifContext.Clients.Group(recruiterId.ToLower()).SendAsync("ReceiveNotification", payload);
                    await telegramBotSvc.SendPushNotificationAsync(recruiterGuid, title, message);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgent-NotifyHR] Lỗi khi gửi thông báo cho HR: {ex.Message}");
            }
        });
    }
}

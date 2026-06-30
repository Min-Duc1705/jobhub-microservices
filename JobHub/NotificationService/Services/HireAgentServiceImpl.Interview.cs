using CommonService.Exceptions;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using NotificationService.Data;
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
                string date1Str = campaign.InterviewDate.HasValue ? campaign.InterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm") : "";
                string date2Str = campaign.BackupInterviewDate.HasValue ? campaign.BackupInterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm") : "";

                // Gọi AI CVIntelligenceService để phân loại ý định qua ngôn ngữ tự nhiên
                string confirmIntent = "unknown";
                try
                {
                    var confirmPayload = new
                    {
                        date1 = date1Str,
                        date2 = date2Str,
                        candidate_message = candidateMessage
                    };
                    
                    var reqMsg = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/cv/hire-agent/classify-intent");
                    reqMsg.Content = new StringContent(JsonSerializer.Serialize(confirmPayload), Encoding.UTF8, "application/json");

                    var resMsg = await _httpClient.SendAsync(reqMsg);
                    if (resMsg.IsSuccessStatusCode)
                    {
                        var confirmJsonDoc = JsonDocument.Parse(await resMsg.Content.ReadAsStringAsync());
                        if (confirmJsonDoc.RootElement.TryGetProperty("intent", out var confirmIntentProp))
                        {
                            confirmIntent = confirmIntentProp.GetString() ?? "unknown";
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[HireAgent-Classifier] Lỗi khi gọi AI phân loại ý định: {ex.Message}");
                }

                if (campaign.InterviewDate.HasValue && campaign.BackupInterviewDate.HasValue)
                {
                    // 1. Ứng viên chọn Phương án 1
                    if (confirmIntent == "confirm_1")
                    {
                        agentConv.InterviewDate = campaign.InterviewDate;
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);
                        await ConfirmInterviewAsync(agentConv.CampaignId, agentConv.CandidateId);
                        return;
                    }

                    // 2. Ứng viên chọn Phương án 2
                    if (confirmIntent == "confirm_2")
                    {
                        agentConv.InterviewDate = campaign.BackupInterviewDate;
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);
                        await ConfirmInterviewAsync(agentConv.CampaignId, agentConv.CandidateId);
                        return;
                    }

                    // 3. Ứng viên muốn đổi lịch / dời giờ
                    if (confirmIntent == "reschedule")
                    {
                        await ProposeRescheduleAsync(agentConv.CampaignId, agentConv.CandidateId, candidateMessage);
                        return;
                    }

                    // 4. Ứng viên muốn từ chối / hủy tuyển dụng
                    if (confirmIntent == "cancel")
                    {
                        agentConv.Status = "Failed";
                        agentConv.InterviewDate = null;
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);

                        var cancelMsg = "[HỆ THỐNG] Đã ghi nhận yêu cầu hủy phỏng vấn và rút hồ sơ của bạn cho vị trí này. Trạng thái ứng tuyển đã chuyển sang Không đạt. Cảm ơn bạn và chúc bạn may mắn!";
                        var sysMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, cancelMsg, "text");
                        await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);
                        await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);

                        var leaveMsg = "[HỆ THỐNG] Trợ lý AI đã rời khỏi cuộc trò chuyện.";
                        var leaveMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, leaveMsg, "text");
                        await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                        await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                        return;
                    }

                    // 5. Mặc định: Nhắc nhở ứng viên chọn rõ 1 trong các phương án
                    var date1Formatted = campaign.InterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm");
                    var date2Formatted = campaign.BackupInterviewDate.Value.ToLocalTime().ToString("dd/MM/yyyy HH:mm");

                    var reminderMsg = $"[HỆ THỐNG] Bạn vui lòng chọn rõ phương án lịch phỏng vấn:\n" +
                                      $"• Nhắn **1** để chọn Phương án 1: **{date1Formatted}**\n" +
                                      $"• Nhắn **2** để chọn Phương án 2: **{date2Formatted}**\n" +
                                      $"• Nhắn **3** hoặc \"Bận cả hai\" nếu bạn muốn đề xuất khung giờ khác.";
                    var reminderResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, reminderMsg, "text");
                    await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", reminderResponse);
                    await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", reminderResponse);
                    return;
                }
                else
                {
                    // Trường hợp chỉ có 1 đề xuất thời gian (lịch phỏng vấn đơn hoặc đặt lịch thủ công)
                    if (confirmIntent == "confirm_general" || confirmIntent == "confirm_1" || confirmIntent == "confirm_2")
                    {
                        await ConfirmInterviewAsync(agentConv.CampaignId, agentConv.CandidateId);
                        return;
                    }

                    if (confirmIntent == "reschedule")
                    {
                        await ProposeRescheduleAsync(agentConv.CampaignId, agentConv.CandidateId, candidateMessage);
                        return;
                    }

                    if (confirmIntent == "cancel")
                    {
                        agentConv.Status = "Failed";
                        agentConv.InterviewDate = null;
                        await _hireAgentRepo.UpdateConversationAsync(agentConv);

                        var cancelMsg = "[HỆ THỐNG] Đã ghi nhận yêu cầu hủy phỏng vấn và rút hồ sơ của bạn cho vị trí này. Trạng thái ứng tuyển đã chuyển sang Không đạt. Cảm ơn bạn và chúc bạn may mắn!";
                        var sysMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, cancelMsg, "text");
                        await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);
                        await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);

                        var leaveMsg = "[HỆ THỐNG] Trợ lý AI đã rời khỏi cuộc trò chuyện.";
                        var leaveMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, leaveMsg, "text");
                        await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                        await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
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

            string intent = "continue";
            if (jsonDoc.RootElement.TryGetProperty("intent", out var intentProp))
            {
                intent = intentProp.GetString() ?? "continue";
            }

            if (intent == "cancel")
            {
                // Chuyển trạng thái sang Failed (Không đạt)
                agentConv.Status = "Failed";
                agentConv.InterviewDate = null;
                await _hireAgentRepo.UpdateConversationAsync(agentConv);

                var cancelMsg = "[HỆ THỐNG] Đã ghi nhận yêu cầu hủy phỏng vấn và rút hồ sơ của bạn cho vị trí này. Trạng thái ứng tuyển đã chuyển sang Không đạt. Cảm ơn bạn và chúc bạn may mắn!";
                var sysMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, cancelMsg, "text");
                await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);
                await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);

                // Gửi thông báo AI đã rời cuộc trò chuyện
                var leaveMsg = "[HỆ THỐNG] Trợ lý AI đã rời khỏi cuộc trò chuyện.";
                var leaveMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, leaveMsg, "text");
                await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                return;
            }

            if (intent == "reschedule")
            {
                // Reset trạng thái về Passed để có thể đặt lịch lại
                agentConv.Status = "Passed";
                agentConv.InterviewDate = null;
                await _hireAgentRepo.UpdateConversationAsync(agentConv);

                var rescheduleMsg = "[HỆ THỐNG] Đã ghi nhận yêu cầu thay đổi lịch hẹn phỏng vấn của bạn. Chúng tôi sẽ thông báo cho chuyên viên nhân sự để sắp xếp và đề xuất khung giờ mới.";
                var sysMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, rescheduleMsg, "text");
                await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);
                await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", sysMsgResponse);

                // Gửi thông báo AI đã rời cuộc trò chuyện
                var leaveMsg = "[HỆ THỐNG] Trợ lý AI đã rời khỏi cuộc trò chuyện để chuẩn bị sắp xếp lịch mới.";
                var leaveMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, leaveMsg, "text");
                await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", leaveMsgResponse);
                return;
            }

            // 3. Gửi tin nhắn trả lời của Agent
            var chatMessageResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, "[AI] " + reply, "text");
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
                        // _ = SendProposalEmailAsync(campaign, agentConv.CandidateId, $"{date1Str} hoặc {date2Str}", chatPageUrl);

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
        var conversation = await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId);
        if (conversation == null)
        {
            conversation = new HireAgentConversation
            {
                Id             = Guid.NewGuid(),
                CampaignId     = campaignId,
                ConversationId = Guid.NewGuid(),
                CandidateId    = candidateId,
                CvText         = "Standard Application Candidate",
                Status         = "PendingCandidateConfirm",
                MatchingScore  = 100.0,
                LastQuestionAt = DateTimeOffset.UtcNow,
                CreatedAt      = DateTimeOffset.UtcNow
            };
            await _hireAgentRepo.CreateConversationAsync(conversation);
        }

        conversation.Status        = "PendingCandidateConfirm";
        conversation.InterviewDate = interviewDate.ToUniversalTime();
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
 
            // Cập nhật lại ConversationId thực tế của cuộc trò chuyện Chat để AI Interceptor có thể khớp chính xác
            conversation.ConversationId = msgResponse.ConversationId;
            await _hireAgentRepo.UpdateConversationAsync(conversation);

            // _ = SendProposalEmailAsync(campaign, candidateId, dateStr, chatPageUrl);
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
                    using var scope = _scopeFactory.CreateScope();
                    var googleCalendarService = scope.ServiceProvider.GetRequiredService<IGoogleCalendarService>();
                    var db = scope.ServiceProvider.GetRequiredService<NotificationDbContext>();

                    var candidateInfo = await UserInfoHelper.GetUserDetailsAsync(candidateId, _config);
                    var candidateName = candidateInfo.FullName ?? "Ứng viên";
                    var notifTitle = "📅 Lịch phỏng vấn được xác nhận";
                    var notifBody = $"Ứng viên {candidateName} đã xác nhận lịch phỏng vấn cho vị trí \"{campaign.JobName}\" vào lúc {dateStr}.";
                    SendNotificationToHr(campaign.RecruiterId, campaignId, candidateId, notifTitle, notifBody, $"hire_agent_scheduled:{campaignId}:{candidateId}");

                    // Đồng bộ lên Google Calendar của Recruiter nếu đã liên kết
                    var isConnected = await googleCalendarService.IsConnectedAsync(campaign.RecruiterId);
                    if (isConnected)
                    {
                        var googleEventId = await googleCalendarService.CreateEventAsync(
                            campaign.RecruiterId,
                            $"[JobHub] Lịch phỏng vấn: {candidateName}",
                            $"Lịch phỏng vấn vòng Final cho vị trí \"{campaign.JobName}\" (Chiến dịch AI Recruiter)",
                            interviewDate,
                            interviewDate.AddHours(1),
                            candidateInfo.Email ?? "candidate@jobhub.com"
                        );

                        if (!string.IsNullOrEmpty(googleEventId))
                        {
                            // Đảm bảo không trùng map cũ
                            var existingMap = await db.InterviewGoogleEvents.FirstOrDefaultAsync(m => m.InterviewId == conversation.Id);
                            if (existingMap != null)
                            {
                                db.InterviewGoogleEvents.Remove(existingMap);
                            }

                            var newMap = new InterviewGoogleEvent
                            {
                                Id = Guid.NewGuid(),
                                InterviewId = conversation.Id,
                                GoogleEventId = googleEventId,
                                RecruiterId = campaign.RecruiterId,
                                CreatedAt = DateTimeOffset.UtcNow
                            };
                            await db.InterviewGoogleEvents.AddAsync(newMap);
                            await db.SaveChangesAsync();
                            Console.WriteLine($"[GoogleCalendar-HireAgent] Đã tự động tạo sự kiện Google Calendar: {googleEventId}");
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[GoogleCalendar-HireAgent] Lỗi khi tạo sự kiện trên Google Calendar: {ex.Message}");
                }
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

    public async Task<HireAgentConversation> CancelInterviewAsync(Guid campaignId, string candidateId)
    {
        var conversation = await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId)
            ?? throw new NotFoundException("Không tìm thấy hội thoại tuyển dụng AI của ứng viên.");

        // Reset về Passed và xóa ngày để quay về trạng thái chưa xếp lịch
        conversation.Status = "Passed";
        conversation.InterviewDate = null;

        await _hireAgentRepo.UpdateConversationAsync(conversation);

        var campaign = await _hireAgentRepo.GetCampaignAsync(campaignId);
        
        // Đồng bộ xóa sự kiện Google Calendar của Recruiter nếu có
        try
        {
            if (campaign != null)
            {
                var map = await _dbContext.InterviewGoogleEvents.FirstOrDefaultAsync(m => m.InterviewId == conversation.Id);
                if (map != null)
                {
                    await _googleCalendarService.DeleteEventAsync(campaign.RecruiterId, map.GoogleEventId);
                    _dbContext.InterviewGoogleEvents.Remove(map);
                    await _dbContext.SaveChangesAsync();
                    Console.WriteLine($"[GoogleCalendar-Cancel] Đã xóa lịch trên Google Calendar ứng với ConversationId: {conversation.Id}");
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[GoogleCalendar-Cancel] Lỗi khi hủy lịch trên Google Calendar: {ex.Message}");
        }

        // Gửi tin nhắn thông báo hủy lịch phỏng vấn đến ứng viên qua Chat
        if (campaign != null)
        {
            var cancelMsg = "[HỆ THỐNG] 🔄 Nhà tuyển dụng đã hủy lịch hẹn phỏng vấn này. Cuộc trò chuyện đã quay trở lại trạng thái chờ xếp lịch phỏng vấn mới.";
            var msgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, candidateId, cancelMsg, "text");
            await _hubContext.Clients.Group(candidateId.ToLower()).SendAsync("ReceiveMessage", msgResponse);
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", msgResponse);
        }

        return conversation;
    }
}

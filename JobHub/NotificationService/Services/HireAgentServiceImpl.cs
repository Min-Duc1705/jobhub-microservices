using CommonService.Exceptions;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Configuration;
using NotificationService.Hubs;
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

public class HireAgentServiceImpl : IHireAgentService
{
    private readonly IHireAgentRepository _hireAgentRepo;
    private readonly IChatRepository _chatRepo;
    private readonly IChatService _chatService;
    private readonly IHubContext<ChatHub> _hubContext;
    private readonly IConfiguration _config;
    private readonly IServiceScopeFactory _scopeFactory;
    private static readonly HttpClient _httpClient = new HttpClient();

    public HireAgentServiceImpl(
        IHireAgentRepository hireAgentRepo,
        IChatRepository chatRepo,
        IChatService chatService,
        IHubContext<ChatHub> hubContext,
        IConfiguration config,
        IServiceScopeFactory scopeFactory)
    {
        _hireAgentRepo = hireAgentRepo;
        _chatRepo = chatRepo;
        _chatService = chatService;
        _hubContext = hubContext;
        _config = config;
        _scopeFactory = scopeFactory;
    }

    public async Task<HireAgentCampaign> CreateCampaignAsync(Guid jobId, string jobName, string jobDescription, string recruiterId, int targetCount, string? jobLocation = null, string? jobType = null)
    {
        if (jobId == Guid.Empty || string.IsNullOrWhiteSpace(jobName) || string.IsNullOrWhiteSpace(jobDescription) || string.IsNullOrWhiteSpace(recruiterId))
        {
            throw new BadRequestException("Thông tin chiến dịch tuyển dụng không hợp lệ.");
        }

        var campaign = new HireAgentCampaign
        {
            Id = Guid.NewGuid(),
            JobId = jobId,
            JobName = jobName.Trim(),
            JobDescription = jobDescription.Trim(),
            RecruiterId = recruiterId,
            TargetCount = targetCount,
            Status = "Active",
            JobLocation = jobLocation?.Trim(),
            JobType = jobType?.Trim().ToUpper(),
            CreatedAt = DateTimeOffset.UtcNow
        };

        await _hireAgentRepo.CreateCampaignAsync(campaign);

        // Kích hoạt tiếp cận ngầm ứng viên không đồng bộ
        _ = Task.Run(async () =>
        {
            try
            {
                using (var scope = _scopeFactory.CreateScope())
                {
                    var svc = scope.ServiceProvider.GetRequiredService<IHireAgentService>();
                    await svc.RunCampaignOutreachAsync(campaign.Id);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgent-Outreach] Lỗi chạy ngầm chiến dịch: {ex.Message}");
            }
        });

        return campaign;
    }

    public async Task<List<HireAgentCampaign>> GetCampaignsByRecruiterAsync(string recruiterId)
    {
        return await _hireAgentRepo.GetCampaignsByRecruiterAsync(recruiterId);
    }

    public async Task<List<HireAgentConversation>> GetConversationsByCampaignAsync(Guid campaignId)
    {
        return await _hireAgentRepo.GetConversationsByCampaignAsync(campaignId);
    }

    public async Task RunCampaignOutreachAsync(Guid campaignId)
    {
        try
        {
            var campaign = await _hireAgentRepo.GetCampaignAsync(campaignId);
            if (campaign == null || campaign.Status != "Active") return;

            // 1. Tạo JWT Token nội bộ để gọi ResumeService
            var secretKey = _config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
            var issuer = _config["Jwt:Issuer"] ?? "JobHub";
            var audience = _config["Jwt:Audience"] ?? "JobHubClient";
            var token = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

            // 2. Lấy danh sách CV từ ResumeService
            var request = new HttpRequestMessage(HttpMethod.Get, "http://resumeservice:8080/api/v1/resumes?pageSize=1000");
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var response = await _httpClient.SendAsync(request);
            if (!response.IsSuccessStatusCode)
            {
                Console.WriteLine($"[HireAgent] Lỗi khi gọi ResumeService: {response.StatusCode}");
                return;
            }

            var contentStr = await response.Content.ReadAsStringAsync();
            var jsonDoc = JsonDocument.Parse(contentStr);
            var resumes = jsonDoc.RootElement.GetProperty("data").GetProperty("result");

            if (resumes.ValueKind != JsonValueKind.Array) return;

            // 3. Quét qua từng CV và so khớp điểm
            // 3. Quét qua toàn bộ CV và lưu trữ điểm số khớp
            var candidateScores = new List<(JsonElement Resume, double Score)>();
            var currentConversations = await _hireAgentRepo.GetConversationsByCampaignAsync(campaignId);

            foreach (var resume in resumes.EnumerateArray())
            {
                var candidateId = resume.GetProperty("customerId").GetString();
                if (string.IsNullOrEmpty(candidateId)) continue;

                // Nếu ứng viên đã có trong campaign này rồi thì bỏ qua
                if (currentConversations.Any(c => c.CandidateId == candidateId)) continue;

                // Kiểm tra trạng thái tìm việc + lấy Province (Quyền riêng tư & Location)
                string? candidateProvince = null;
                try
                {
                    var profileReq = new HttpRequestMessage(HttpMethod.Get, $"http://profileservice:8080/api/v1/customers/{candidateId}");
                    profileReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                    var profileRes = await _httpClient.SendAsync(profileReq);
                    if (profileRes.IsSuccessStatusCode)
                    {
                        var profileStr = await profileRes.Content.ReadAsStringAsync();
                        var profileDoc = JsonDocument.Parse(profileStr);
                        var dataElement = profileDoc.RootElement.GetProperty("data");

                        // Check JobSearchStatus
                        if (dataElement.TryGetProperty("jobSearchStatus", out var statusProp) && statusProp.ValueKind != JsonValueKind.Null)
                        {
                            var statusVal = statusProp.ValueKind == JsonValueKind.Number 
                                ? statusProp.GetInt32().ToString() 
                                : statusProp.GetString();
                            if (statusVal == "NOT_LOOKING" || statusVal == "2")
                            {
                                Console.WriteLine($"[HireAgent-Outreach] Bỏ qua ứng viên {candidateId} do trạng thái tìm việc là NOT_LOOKING.");
                                continue;
                            }
                        }

                        // Lấy Address từ profile (bao gồm cả Tỉnh/Thành + Phường/Xã)
                        if (dataElement.TryGetProperty("address", out var addrProp) && addrProp.ValueKind != JsonValueKind.Null)
                        {
                            var fullAddress = addrProp.GetString() ?? "";
                            // Extract tỉnh/thành từ address string
                            candidateProvince = _ExtractLocationFromCvText(fullAddress);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[HireAgent-Outreach] Lỗi khi kiểm tra profile ứng viên {candidateId}: {ex.Message}");
                }

                string? cvText = null;
                if (resume.TryGetProperty("extractedText", out var extVal) && extVal.ValueKind != JsonValueKind.Null)
                {
                    cvText = extVal.GetString();
                }
                if (string.IsNullOrWhiteSpace(cvText) && resume.TryGetProperty("contentJson", out var jsonVal) && jsonVal.ValueKind != JsonValueKind.Null)
                {
                    cvText = jsonVal.GetString();
                }
                if (string.IsNullOrWhiteSpace(cvText)) continue;

                // ── Chặn cứng theo Province từ Profile ───────────────────────────
                // Dùng profile.Province (người dùng nhập khi đăng ký) — chính xác nhất
                var isRemoteJob = campaign.JobType == "REMOTE" || campaign.JobType == "HYBRID";
                if (!isRemoteJob && !string.IsNullOrWhiteSpace(campaign.JobLocation))
                {
                    if (!string.IsNullOrWhiteSpace(candidateProvince))
                    {
                        if (!_IsLocationMatch(campaign.JobLocation, candidateProvince))
                        {
                            Console.WriteLine($"[HireAgent-Location] Loại ứng viên {candidateId}: tỉnh '{candidateProvince}' không khớp job tại '{campaign.JobLocation}'");
                            continue;
                        }
                        Console.WriteLine($"[HireAgent-Location] ✓ Ứng viên {candidateId}: '{candidateProvince}' khớp '{campaign.JobLocation}'");
                    }
                    // Nếu profile chưa có Province → không chặn (benefit of doubt)
                }

                // Gọi CVIntelligenceService để chấm điểm CV
                var scorePayload = new
                {
                    job_description = campaign.JobDescription,
                    cv_text = cvText
                };
                var scoreReq = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/cv/score");
                scoreReq.Content = new StringContent(JsonSerializer.Serialize(scorePayload), Encoding.UTF8, "application/json");

                try
                {
                    var scoreRes = await _httpClient.SendAsync(scoreReq);
                    if (!scoreRes.IsSuccessStatusCode) continue;

                    var scoreStr = await scoreRes.Content.ReadAsStringAsync();
                    var scoreDoc = JsonDocument.Parse(scoreStr);
                    double matchingScore = scoreDoc.RootElement.GetProperty("data").GetProperty("matching_score").GetDouble();

                    Console.WriteLine($"[HireAgent-Score] Ứng viên {candidateId}: {matchingScore:F1} điểm");

                    // Ngưỡng tối thiểu 30 điểm (sau khi đã áp Hard Skill Penalty từ CVIntelligenceService)
                    // Ứng viên sai domain hoàn toàn sẽ bị penalty ×0.2 → score ~8-15 → bị loại
                    // Ứng viên đúng domain sẽ có score >= 35-40 sau penalty → lọt vào pool
                    if (matchingScore >= 30.0)
                    {
                        candidateScores.Add((resume, matchingScore));
                    }
                    else
                    {
                        Console.WriteLine($"[HireAgent-Score] Loại ứng viên {candidateId}: điểm {matchingScore:F1} < 30 (không đủ tiêu chuẩn)");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[HireAgent-Score] Lỗi khi chấm điểm ứng viên {candidateId}: {ex.Message}");
                }
            }

            // 4. Sort giảm dần theo điểm — chỉ lấy top targetCount ứng viên phù hợp nhất
            var sortedCandidates = candidateScores
                .OrderByDescending(x => x.Score)
                .Take(campaign.TargetCount)
                .ToList();

            Console.WriteLine($"[HireAgent] Tổng pool đạt chuẩn: {candidateScores.Count} ứng viên → tiếp cận top {sortedCandidates.Count}");
            int invitedCount = 0;

            foreach (var item in sortedCandidates)
            {
                if (currentConversations.Count + invitedCount >= campaign.TargetCount) break;

                var resume = item.Resume;
                var candidateId = resume.GetProperty("customerId").GetString()!;
                string? cvText = null;
                if (resume.TryGetProperty("extractedText", out var extVal2) && extVal2.ValueKind != JsonValueKind.Null)
                {
                    cvText = extVal2.GetString();
                }
                if (string.IsNullOrWhiteSpace(cvText) && resume.TryGetProperty("contentJson", out var jsonVal2) && jsonVal2.ValueKind != JsonValueKind.Null)
                {
                    cvText = jsonVal2.GetString();
                }
                if (string.IsNullOrWhiteSpace(cvText)) continue;

                var recruiterMeta = await GetRecruiterAndCompanyDetailsAsync(campaign.RecruiterId);
                var frontendUrl = _config["FrontendUrl"] ?? "http://localhost:5173";
                var jobUrl = $"{frontendUrl.TrimEnd('/')}/jobs/{campaign.JobId}";

                // Sinh lời mời mở đầu chào hỏi cá nhân hóa
                var chatPayload = new
                {
                    job_description = campaign.JobDescription,
                    cv_text = cvText,
                    chat_history = new List<object>(),
                    recruiter_name = recruiterMeta.RecruiterName,
                    company_name = recruiterMeta.CompanyName,
                    job_name = campaign.JobName,
                    job_url = jobUrl
                };
                var chatReq = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/cv/hire-agent/chat");
                chatReq.Content = new StringContent(JsonSerializer.Serialize(chatPayload), Encoding.UTF8, "application/json");

                try
                {
                    var chatRes = await _httpClient.SendAsync(chatReq);
                    if (!chatRes.IsSuccessStatusCode) continue;

                    var chatStr = await chatRes.Content.ReadAsStringAsync();
                    var chatDoc = JsonDocument.Parse(chatStr);
                    var welcomeMsg = chatDoc.RootElement.GetProperty("reply").GetString()
                        ?? $"Chào bạn, tôi là trợ lý AI tuyển dụng của {campaign.JobName}. Tôi thấy hồ sơ của bạn rất ấn tượng và muốn trao đổi cơ hội làm việc!";

                    // Tạo cuộc hội thoại chat thực tế đại diện cho HR
                    var chatMessageResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, candidateId, welcomeMsg, "text");

                    // Tạo HireAgentConversation trong database
                    var agentConv = new HireAgentConversation
                    {
                        Id = Guid.NewGuid(),
                        CampaignId = campaignId,
                        ConversationId = chatMessageResponse.ConversationId,
                        CandidateId = candidateId,
                        CvText = cvText,
                        Status = "Screening",
                        MatchingScore = item.Score,
                        LastQuestionAt = DateTimeOffset.UtcNow,
                        CreatedAt = DateTimeOffset.UtcNow
                    };
                    await _hireAgentRepo.CreateConversationAsync(agentConv);

                    // Gửi tin nhắn real-time thông qua SignalR tới cả ứng viên và nhà tuyển dụng
                    await _hubContext.Clients.Group(candidateId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);
                    await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);

                    invitedCount++;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[HireAgent-Outreach] Lỗi khi tiếp cận ứng viên {candidateId}: {ex.Message}");
                }
            }

            bool hasNewInvites = invitedCount > 0;

            // Cập nhật trạng thái chiến dịch
            if (currentConversations.Count + invitedCount >= campaign.TargetCount)
            {
                campaign.Status = "Completed";
            }
            await _hireAgentRepo.UpdateCampaignAsync(campaign);

            // Báo SignalR cho Recruiter biết tiến trình chạy ngầm đã xong và gửi status mới
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("CampaignStatusChanged", new
            {
                CampaignId = campaignId,
                Status = campaign.Status
            });

            // Nếu có ứng viên mới được mời, báo cho Recruiter biết để reload danh sách ứng viên
            if (hasNewInvites)
            {
                await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("CampaignConversationsUpdated", new
                {
                    CampaignId = campaignId
                });
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[HireAgent] Lỗi trong tiến trình chạy chiến dịch: {ex.Message}");
        }
    }

    public async Task ProcessCandidateReplyAsync(Guid chatConversationId, string candidateMessage)
    {
        try
        {
            var agentConv = await _hireAgentRepo.GetActiveConversationByChatIdAsync(chatConversationId);
            if (agentConv == null) return;

            var campaign = await _hireAgentRepo.GetCampaignAsync(agentConv.CampaignId);
            if (campaign == null) return;

            // 1. Lấy lịch sử chat
            var messages = await _chatRepo.GetMessagesForConversationAsync(chatConversationId, 15, null);
            var orderedMsgs = messages.OrderBy(m => m.CreatedAt).ToList();

            var chatHistory = new List<object>();
            foreach (var msg in orderedMsgs)
            {
                chatHistory.Add(new
                {
                    sender = msg.SenderId.Equals(agentConv.CandidateId, StringComparison.OrdinalIgnoreCase) ? "candidate" : "agent",
                    content = msg.Content
                });
            }

            var recruiterMeta = await GetRecruiterAndCompanyDetailsAsync(campaign.RecruiterId);
            var frontendUrl = _config["FrontendUrl"] ?? "http://localhost:5173";
            var jobUrl = $"{frontendUrl.TrimEnd('/')}/jobs/{campaign.JobId}";

            // 2. Gửi lịch sử chat lên CVIntelligenceService để nhận câu trả lời tiếp theo
            var payload = new
            {
                job_description = campaign.JobDescription,
                cv_text = agentConv.CvText,
                chat_history = chatHistory,
                recruiter_name = recruiterMeta.RecruiterName,
                company_name = recruiterMeta.CompanyName,
                job_name = campaign.JobName,
                job_url = jobUrl
            };

            var request = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/cv/hire-agent/chat");
            request.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

            var response = await _httpClient.SendAsync(request);
            if (!response.IsSuccessStatusCode) return;

            var contentStr = await response.Content.ReadAsStringAsync();
            var jsonDoc = JsonDocument.Parse(contentStr);
            var reply = jsonDoc.RootElement.GetProperty("reply").GetString() ?? "";
            bool isCompleted = jsonDoc.RootElement.GetProperty("is_completed").GetBoolean();
            bool isPassed = jsonDoc.RootElement.GetProperty("is_passed").GetBoolean();

            // 3. Gửi tin nhắn trả lời của Agent
            var chatMessageResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, reply, "text");

            // Phát tín hiệu SignalR real-time cho cả Candidate và Recruiter
            await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);

            // 4. Nếu phỏng vấn sàng lọc hoàn thành
            if (isCompleted)
            {
                agentConv.Status = isPassed ? "Passed" : "Failed";
                await _hireAgentRepo.UpdateConversationAsync(agentConv);

                if (isPassed)
                {
                    // Tự động chèn link chốt lịch hẹn
                    frontendUrl = _config["FrontendUrl"] ?? "http://localhost:5173";
                    var scheduleMsg = $"[HỆ THỐNG] Chúc mừng bạn đã vượt qua vòng sàng lọc sơ bộ! Hãy bấm vào liên kết sau để đặt lịch phỏng vấn chính thức với tôi: {frontendUrl.TrimEnd('/')}/schedule/{campaign.Id}";
                    var scheduleMessageResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, scheduleMsg, "text");
                    await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", scheduleMessageResponse);
                }
                else
                {
                    // Tự động thông báo AI đã rời cuộc trò chuyện khi không đạt
                    var leaveMsg = "[HỆ THỐNG] Trợ lý AI đã kết thúc buổi đánh giá và rời khỏi cuộc trò chuyện.";
                    var leaveMessageResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, agentConv.CandidateId, leaveMsg, "text");
                    await _hubContext.Clients.Group(agentConv.CandidateId.ToLower()).SendAsync("ReceiveMessage", leaveMessageResponse);
                    await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", leaveMessageResponse);
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

    public async Task<HireAgentCampaign?> GetCampaignByIdAsync(Guid campaignId)
    {
        return await _hireAgentRepo.GetCampaignAsync(campaignId);
    }

    public async Task<HireAgentConversation> ScheduleInterviewAsync(Guid campaignId, string candidateId, DateTimeOffset interviewDate)
    {
        var conversation = await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId);
        if (conversation == null)
        {
            throw new NotFoundException("Không tìm thấy hội thoại tuyển dụng AI của ứng viên.");
        }

        conversation.Status = "Scheduled";
        conversation.InterviewDate = interviewDate;
        await _hireAgentRepo.UpdateConversationAsync(conversation);

        // Gửi tin nhắn tự động từ hệ thống thông báo đặt lịch thành công
        var campaign = await _hireAgentRepo.GetCampaignAsync(campaignId);
        if (campaign != null)
        {
            var dateStr = interviewDate.ToLocalTime().ToString("dd/MM/yyyy HH:mm");
            var notificationMsg = $"[HỆ THỐNG] Bạn đã đặt lịch hẹn phỏng vấn thành công vào lúc {dateStr}. Hẹn gặp bạn ở buổi phỏng vấn!";
            var systemMsgResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, candidateId, notificationMsg, "text");
            
            // Phát SignalR real-time báo tin nhắn mới
            await _hubContext.Clients.Group(candidateId.ToLower()).SendAsync("ReceiveMessage", systemMsgResponse);
            await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", systemMsgResponse);

            // Gửi email tự động thông báo chốt lịch dưới nền không đồng bộ
            _ = Task.Run(async () =>
            {
                try
                {
                    using (var scope = _scopeFactory.CreateScope())
                    {
                        var emailSvc = scope.ServiceProvider.GetRequiredService<IEmailService>();
                        
                        // Lấy thông tin ứng viên
                        var candidateInfo = await GetCandidateDetailsAsync(candidateId);
                        // Lấy thông tin nhà tuyển dụng (tên, công ty, email)
                        var recruiterMeta = await GetRecruiterAndCompanyDetailsAsync(campaign.RecruiterId);

                        var formattedDateStr = interviewDate.ToLocalTime().ToString("dd/MM/yyyy HH:mm");
                        var frontendUrl = _config["FrontendUrl"] ?? "http://localhost:5173";
                        var candidateChatUrl = $"{frontendUrl.TrimEnd('/')}/chat";

                        // Xây dựng dòng người liên hệ cá nhân hóa theo yêu cầu
                        var recruiterDisplay = $"Trợ lý AI đại diện cho {recruiterMeta.RecruiterName ?? "Nhà tuyển dụng"} thuộc {recruiterMeta.CompanyName ?? "đối tác JobHub"}";

                        if (candidateInfo.Email != null)
                        {
                            // Gửi email cho Ứng viên
                            await emailSvc.SendInterviewEmailAsync(
                                candidateInfo.Email,
                                candidateInfo.FullName ?? "Ứng viên",
                                campaign.JobName,
                                formattedDateStr,
                                recruiterDisplay,
                                candidateChatUrl
                            );
                            Console.WriteLine($"[HireAgent-Email] Đã gửi email xác nhận lịch phỏng vấn đến ứng viên {candidateInfo.Email}");
                        }
                        
                        if (recruiterMeta.Email != null)
                        {
                            var recruiterDashboardUrl = $"{frontendUrl.TrimEnd('/')}/admin/hire-agent";
                            // Gửi email thông báo cho Nhà tuyển dụng
                            await emailSvc.SendInterviewEmailToRecruiterAsync(
                                recruiterMeta.Email,
                                candidateInfo.FullName ?? "Ứng viên",
                                campaign.JobName,
                                formattedDateStr,
                                recruiterMeta.RecruiterName ?? "Nhà tuyển dụng",
                                recruiterDashboardUrl
                            );
                            Console.WriteLine($"[HireAgent-Email] Đã gửi email thông báo lịch phỏng vấn đến nhà tuyển dụng {recruiterMeta.Email}");
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[HireAgent-Email] Lỗi gửi email tự động sau chốt lịch: {ex.Message}");
                }
            });
        }

        return conversation;
    }

    private async Task<(string? Email, string? FullName)> GetCandidateDetailsAsync(string candidateId)
    {
        try
        {
            var secretKey = _config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
            var issuer = _config["Jwt:Issuer"] ?? "JobHub";
            var audience = _config["Jwt:Audience"] ?? "JobHubClient";
            var token = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

            // 1. Gọi ProfileService để lấy thông tin profile (FullName và AppUserId)
            var profileReq = new HttpRequestMessage(HttpMethod.Get, $"http://profileservice:8080/api/v1/customers/{candidateId}");
            profileReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var profileRes = await _httpClient.SendAsync(profileReq);
            if (!profileRes.IsSuccessStatusCode) return (null, null);

            var profileStr = await profileRes.Content.ReadAsStringAsync();
            var profileDoc = JsonDocument.Parse(profileStr);
            var dataElement = profileDoc.RootElement.GetProperty("data");
            
            var fullName = dataElement.TryGetProperty("fullName", out var fnProp) ? fnProp.GetString() : null;
            var appUserId = dataElement.TryGetProperty("appUserId", out var auProp) ? auProp.GetString() : null;

            if (string.IsNullOrEmpty(appUserId)) return (null, fullName);

            // 2. Gọi AuthService để lấy Email từ AppUser
            var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{appUserId}");
            userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var userRes = await _httpClient.SendAsync(userReq);
            if (!userRes.IsSuccessStatusCode) return (null, fullName);

            var userStr = await userRes.Content.ReadAsStringAsync();
            var userDoc = JsonDocument.Parse(userStr);
            var email = userDoc.RootElement.GetProperty("data").GetProperty("email").GetString();

            return (email, fullName);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[HireAgent-Email] Lỗi lấy thông tin chi tiết ứng viên: {ex.Message}");
            return (null, null);
        }
    }

    private async Task<(string? Email, string? FullName)> GetRecruiterDetailsAsync(string recruiterId)
    {
        try
        {
            var secretKey = _config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
            var issuer = _config["Jwt:Issuer"] ?? "JobHub";
            var audience = _config["Jwt:Audience"] ?? "JobHubClient";
            var token = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

            // 1. Gọi ProfileService để lấy thông tin profile (FullName và AppUserId)
            var profileReq = new HttpRequestMessage(HttpMethod.Get, $"http://profileservice:8080/api/v1/customers/{recruiterId}");
            profileReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var profileRes = await _httpClient.SendAsync(profileReq);
            if (!profileRes.IsSuccessStatusCode) return (null, null);

            var profileStr = await profileRes.Content.ReadAsStringAsync();
            var profileDoc = JsonDocument.Parse(profileStr);
            var dataElement = profileDoc.RootElement.GetProperty("data");
            
            var fullName = dataElement.TryGetProperty("fullName", out var fnProp) ? fnProp.GetString() : null;
            var appUserId = dataElement.TryGetProperty("appUserId", out var auProp) ? auProp.GetString() : null;

            if (string.IsNullOrEmpty(appUserId)) return (null, fullName);

            // 2. Gọi AuthService để lấy Email từ AppUser
            var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{appUserId}");
            userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var userRes = await _httpClient.SendAsync(userReq);
            if (!userRes.IsSuccessStatusCode) return (null, fullName);

            var userStr = await userRes.Content.ReadAsStringAsync();
            var userDoc = JsonDocument.Parse(userStr);
            var email = userDoc.RootElement.GetProperty("data").GetProperty("email").GetString();

            return (email, fullName);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[HireAgent-Email] Lỗi lấy thông tin chi tiết nhà tuyển dụng: {ex.Message}");
            return (null, null);
        }
    }

    private async Task<(string? RecruiterName, string? CompanyName, string? Email)> GetRecruiterAndCompanyDetailsAsync(string recruiterId)
    {
        try
        {
            var secretKey = _config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
            var issuer = _config["Jwt:Issuer"] ?? "JobHub";
            var audience = _config["Jwt:Audience"] ?? "JobHubClient";
            var token = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

            // 1. Gọi ProfileService để lấy thông tin profile (FullName, CompanyId, AppUserId)
            var profileReq = new HttpRequestMessage(HttpMethod.Get, $"http://profileservice:8080/api/v1/customers/{recruiterId}");
            profileReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var profileRes = await _httpClient.SendAsync(profileReq);
            if (!profileRes.IsSuccessStatusCode) return (null, null, null);

            var profileStr = await profileRes.Content.ReadAsStringAsync();
            var profileDoc = JsonDocument.Parse(profileStr);
            var dataElement = profileDoc.RootElement.GetProperty("data");
            
            var recruiterName = dataElement.TryGetProperty("fullName", out var fnProp) ? fnProp.GetString() : null;
            var companyIdStr = dataElement.TryGetProperty("companyId", out var compProp) ? compProp.GetString() : null;
            var appUserId = dataElement.TryGetProperty("appUserId", out var auProp) ? auProp.GetString() : null;

            string? compName = null;
            if (!string.IsNullOrEmpty(companyIdStr))
            {
                // 2. Gọi CompanyService để lấy CompanyName từ CompanyId
                var compReq = new HttpRequestMessage(HttpMethod.Get, $"http://companyservice:8080/api/v1/companies/{companyIdStr}");
                compReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                var compRes = await _httpClient.SendAsync(compReq);
                if (compRes.IsSuccessStatusCode)
                {
                    var compStr = await compRes.Content.ReadAsStringAsync();
                    var compDoc = JsonDocument.Parse(compStr);
                    compName = compDoc.RootElement.GetProperty("data").GetProperty("name").GetString();
                }
            }

            string? email = null;
            if (!string.IsNullOrEmpty(appUserId))
            {
                // 3. Gọi AuthService để lấy Email từ AppUser
                var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{appUserId}");
                userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                var userRes = await _httpClient.SendAsync(userReq);
                if (userRes.IsSuccessStatusCode)
                {
                    var userStr = await userRes.Content.ReadAsStringAsync();
                    var userDoc = JsonDocument.Parse(userStr);
                    email = userDoc.RootElement.GetProperty("data").GetProperty("email").GetString();
                }
            }

            return (recruiterName, compName, email);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[HireAgent-Outreach] Lỗi lấy thông tin chi tiết Recruiter/Company: {ex.Message}");
            return (null, null, null);
        }
    }

    public async Task<HireAgentConversation?> GetConversationByCandidateAndCampaignAsync(Guid campaignId, string candidateId)
    {
        return await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId);
    }

    /// <summary>
    /// Extract tên tỉnh/thành phố từ CV text.
    /// Scan toàn bộ CV, trả về tỉnh/thành đầu tiên tìm thấy.
    /// </summary>
    private static string _ExtractLocationFromCvText(string cvText)
    {
        if (string.IsNullOrWhiteSpace(cvText)) return "";

        var cvNorm = _NormalizeLocation(cvText);

        // Danh sách 63 tỉnh/thành + alias phổ biến (đã normalize không dấu)
        var provinces = new[]
        {
            "ho chi minh", "ha noi", "da nang", "can tho", "hai phong",
            "binh duong", "dong nai", "ba ria vung tau", "vung tau",
            "long an", "tien giang", "ben tre", "tra vinh", "vinh long",
            "dong thap", "an giang", "kien giang", "hau giang", "soc trang",
            "bac lieu", "ca mau", "tay ninh", "binh phuoc", "binh thuan",
            "ninh thuan", "khanh hoa", "nha trang", "phu yen", "binh dinh",
            "quang ngai", "quang nam", "hoi an", "thua thien hue", "hue",
            "quang tri", "quang binh", "ha tinh", "nghe an", "vinh",
            "thanh hoa", "ninh binh", "nam dinh", "thai binh", "ha nam",
            "hung yen", "hai duong", "bac ninh", "vinh phuc", "phu tho",
            "tuyen quang", "yen bai", "lao cai", "ha giang", "cao bang",
            "bac kan", "lang son", "thai nguyen", "bac giang", "quang ninh",
            "ha long", "dien bien", "lai chau", "son la", "hoa binh",
            "dak lak", "buon ma thuot", "dak nong", "gia lai", "pleiku",
            "kon tum", "lam dong", "da lat", "binh long", "thu duc",
        };

        foreach (var province in provinces)
        {
            if (cvNorm.Contains(province))
                return province;
        }

        return "";
    }

    /// <summary>
    /// So khớp địa chỉ ứng viên với vị trí job.
    /// Normalize: bỏ dấu, lowercase, alias (hcm=hồ chí minh, hn=hà nội...).
    /// Return true nếu match (hoặc không đủ thông tin để chặn).
    /// </summary>
    private static bool _IsLocationMatch(string jobLocation, string candidateLocation)
    {
        if (string.IsNullOrWhiteSpace(jobLocation) || string.IsNullOrWhiteSpace(candidateLocation))
            return true;

        var jobNorm = _NormalizeLocation(jobLocation);
        var candNorm = _NormalizeLocation(candidateLocation);

        return candNorm.Contains(jobNorm) || jobNorm.Contains(candNorm);
    }

    private static string _NormalizeLocation(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return "";
        var s = text.ToLowerInvariant().Trim();
        s = s.Replace("à","a").Replace("á","a").Replace("ả","a").Replace("ã","a").Replace("ạ","a")
             .Replace("ă","a").Replace("ắ","a").Replace("ặ","a").Replace("ằ","a").Replace("ẵ","a").Replace("ẳ","a")
             .Replace("â","a").Replace("ấ","a").Replace("ầ","a").Replace("ẩ","a").Replace("ẫ","a").Replace("ậ","a")
             .Replace("đ","d")
             .Replace("è","e").Replace("é","e").Replace("ẻ","e").Replace("ẽ","e").Replace("ẹ","e")
             .Replace("ê","e").Replace("ế","e").Replace("ề","e").Replace("ể","e").Replace("ễ","e").Replace("ệ","e")
             .Replace("ì","i").Replace("í","i").Replace("ỉ","i").Replace("ĩ","i").Replace("ị","i")
             .Replace("ò","o").Replace("ó","o").Replace("ỏ","o").Replace("õ","o").Replace("ọ","o")
             .Replace("ô","o").Replace("ố","o").Replace("ồ","o").Replace("ổ","o").Replace("ỗ","o").Replace("ộ","o")
             .Replace("ơ","o").Replace("ớ","o").Replace("ờ","o").Replace("ở","o").Replace("ỡ","o").Replace("ợ","o")
             .Replace("ù","u").Replace("ú","u").Replace("ủ","u").Replace("ũ","u").Replace("ụ","u")
             .Replace("ư","u").Replace("ứ","u").Replace("ừ","u").Replace("ử","u").Replace("ữ","u").Replace("ự","u")
             .Replace("ỳ","y").Replace("ý","y").Replace("ỷ","y").Replace("ỹ","y").Replace("ỵ","y");
        s = s.Replace("tp. ho chi minh","ho chi minh").Replace("tp.ho chi minh","ho chi minh")
             .Replace("tp ho chi minh","ho chi minh").Replace("thanh pho ho chi minh","ho chi minh")
             .Replace("sai gon","ho chi minh").Replace("tphcm","ho chi minh").Replace("hcm","ho chi minh")
             .Replace("thu do ha noi","ha noi").Replace("thanh pho da nang","da nang")
             .Replace("bien hoa","dong nai").Replace("thu duc","ho chi minh");
        return s.Trim();
    }
}

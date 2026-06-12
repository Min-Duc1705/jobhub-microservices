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
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace NotificationService.Services;

// Partial class — phần xử lý chiến dịch tuyển dụng (Campaign & Outreach)
public partial class HireAgentServiceImpl
{
    public async Task<HireAgentCampaign> CreateCampaignAsync(
        Guid jobId, string jobName, string jobDescription, string recruiterId,
        int targetCount, string? jobLocation = null, string? jobType = null)
    {
        if (jobId == Guid.Empty || string.IsNullOrWhiteSpace(jobName)
            || string.IsNullOrWhiteSpace(jobDescription) || string.IsNullOrWhiteSpace(recruiterId))
            throw new CommonService.Exceptions.BadRequestException("Thông tin chiến dịch tuyển dụng không hợp lệ.");

        var campaign = new HireAgentCampaign
        {
            Id            = Guid.NewGuid(),
            JobId         = jobId,
            JobName       = jobName.Trim(),
            JobDescription = jobDescription.Trim(),
            RecruiterId   = recruiterId,
            TargetCount   = targetCount,
            Status        = "Active",
            JobLocation   = jobLocation?.Trim(),
            JobType       = jobType?.Trim().ToUpper(),
            CreatedAt     = DateTimeOffset.UtcNow
        };

        await _hireAgentRepo.CreateCampaignAsync(campaign);

        // Kích hoạt tiếp cận ngầm ứng viên không đồng bộ
        _ = Task.Run(async () =>
        {
            try
            {
                using var scope = _scopeFactory.CreateScope();
                var svc = scope.ServiceProvider.GetRequiredService<IHireAgentService>();
                await svc.RunCampaignOutreachAsync(campaign.Id);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgent-Outreach] Lỗi chạy ngầm chiến dịch: {ex.Message}");
            }
        });

        return campaign;
    }

    public async Task<List<HireAgentCampaign>> GetCampaignsByRecruiterAsync(string recruiterId) =>
        await _hireAgentRepo.GetCampaignsByRecruiterAsync(recruiterId);

    public async Task<List<HireAgentConversation>> GetConversationsByCampaignAsync(Guid campaignId) =>
        await _hireAgentRepo.GetConversationsByCampaignAsync(campaignId);

    public async Task<HireAgentCampaign?> GetCampaignByIdAsync(Guid campaignId) =>
        await _hireAgentRepo.GetCampaignAsync(campaignId);

    public async Task<HireAgentConversation?> GetConversationByCandidateAndCampaignAsync(Guid campaignId, string candidateId) =>
        await _hireAgentRepo.GetConversationByCandidateAndCampaignAsync(candidateId, campaignId);

    public async Task RunCampaignOutreachAsync(Guid campaignId)
    {
        if (!_runningCampaigns.TryAdd(campaignId, true))
        {
            Console.WriteLine($"[HireAgent] Chiến dịch {campaignId} đang chạy trong luồng khác, bỏ qua.");
            return;
        }
        try
        {
            try
            {
                var campaign = await _hireAgentRepo.GetCampaignAsync(campaignId);
                if (campaign == null || campaign.Status != "Active") return;

                // 1. Tạo JWT Token nội bộ
                var secretKey = _config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
                var issuer    = _config["Jwt:Issuer"]    ?? "JobHub";
                var audience  = _config["Jwt:Audience"]  ?? "JobHubClient";
                var token     = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

                // 2. Lấy danh sách CV từ ResumeService
                var request = new HttpRequestMessage(HttpMethod.Get, "http://resumeservice:8080/api/v1/resumes?pageSize=2000");
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                var response = await _httpClient.SendAsync(request);
                if (!response.IsSuccessStatusCode)
                {
                    Console.WriteLine($"[HireAgent] Lỗi khi gọi ResumeService: {response.StatusCode}");
                    return;
                }

                var jsonDoc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
                var resumes = jsonDoc.RootElement.GetProperty("data").GetProperty("result");
                if (resumes.ValueKind != JsonValueKind.Array) return;

                // 3. Quét qua CV — lọc trùng, check location, chấm điểm
                var candidateScores    = new List<(JsonElement Resume, double Score)>();
                var currentConversations = await _hireAgentRepo.GetConversationsByCampaignAsync(campaignId);

                var uniqueResumes = new List<JsonElement>();
                var seenCandidates = new HashSet<string>();
                foreach (var resume in resumes.EnumerateArray())
                {
                    var cid = resume.GetProperty("customerId").GetString();
                    if (!string.IsNullOrEmpty(cid) && seenCandidates.Add(cid))
                        uniqueResumes.Add(resume);
                }

                var semaphore = new System.Threading.SemaphoreSlim(15);
                var tasks = uniqueResumes.Select(async resume =>
                {
                    var candidateId = resume.GetProperty("customerId").GetString();
                    if (string.IsNullOrEmpty(candidateId)) return;

                    if (currentConversations.Any(c => c.CandidateId == candidateId)) return;

                    // Kiểm tra trạng thái tìm việc + Province từ ProfileService
                    string? candidateProvince = null;
                    try
                    {
                        var profileReq = new HttpRequestMessage(HttpMethod.Get, $"http://profileservice:8080/api/v1/customers/{candidateId}");
                        profileReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                        await semaphore.WaitAsync();
                        try
                        {
                            var profileRes = await _httpClient.SendAsync(profileReq);
                            if (profileRes.IsSuccessStatusCode)
                            {
                                var profileDoc = JsonDocument.Parse(await profileRes.Content.ReadAsStringAsync());
                                var dataElement = profileDoc.RootElement.GetProperty("data");

                                if (dataElement.TryGetProperty("jobSearchStatus", out var statusProp)
                                    && statusProp.ValueKind != JsonValueKind.Null)
                                {
                                    var statusVal = statusProp.ValueKind == JsonValueKind.Number
                                        ? statusProp.GetInt32().ToString()
                                        : statusProp.GetString();
                                    if (statusVal == "NOT_LOOKING" || statusVal == "2")
                                    {
                                        Console.WriteLine($"[HireAgent-Outreach] Bỏ qua ứng viên {candidateId}: NOT_LOOKING.");
                                        return;
                                    }
                                }

                                if (dataElement.TryGetProperty("address", out var addrProp)
                                    && addrProp.ValueKind != JsonValueKind.Null)
                                    candidateProvince = LocationHelper.ExtractProvince(addrProp.GetString() ?? "");
                            }
                        }
                        finally { semaphore.Release(); }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[HireAgent-Outreach] Lỗi kiểm tra profile {candidateId}: {ex.Message}");
                    }

                    // Chặn theo Province
                    var isRemoteJob = campaign.JobType == "REMOTE" || campaign.JobType == "HYBRID";
                    if (!isRemoteJob && !string.IsNullOrWhiteSpace(campaign.JobLocation))
                    {
                        if (!string.IsNullOrWhiteSpace(candidateProvince)
                            && !LocationHelper.IsLocationMatch(campaign.JobLocation, candidateProvince))
                        {
                            Console.WriteLine($"[HireAgent-Location] Loại {candidateId}: '{candidateProvince}' ≠ '{campaign.JobLocation}'");
                            return;
                        }
                    }

                    // Lấy CV text
                    string? cvText = null;
                    if (resume.TryGetProperty("extractedText", out var extVal) && extVal.ValueKind != JsonValueKind.Null)
                        cvText = extVal.GetString();
                    if (string.IsNullOrWhiteSpace(cvText)
                        && resume.TryGetProperty("contentJson", out var jsonVal) && jsonVal.ValueKind != JsonValueKind.Null)
                        cvText = jsonVal.GetString();
                    if (string.IsNullOrWhiteSpace(cvText)) return;

                    // Chấm điểm CV qua CVIntelligenceService
                    var scorePayload = new { job_description = campaign.JobDescription, cv_text = cvText, generate_feedback = false };
                    var scoreReq = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/cv/score");
                    scoreReq.Content = new StringContent(JsonSerializer.Serialize(scorePayload), Encoding.UTF8, "application/json");

                    await semaphore.WaitAsync();
                    try
                    {
                        var scoreRes = await _httpClient.SendAsync(scoreReq);
                        if (!scoreRes.IsSuccessStatusCode) return;

                        var scoreDoc = JsonDocument.Parse(await scoreRes.Content.ReadAsStringAsync());
                        double matchingScore = scoreDoc.RootElement.GetProperty("data").GetProperty("matching_score").GetDouble();
                        Console.WriteLine($"[HireAgent-Score] {candidateId}: {matchingScore:F1} điểm");

                        if (matchingScore >= 50.0)
                            lock (candidateScores) { candidateScores.Add((resume, matchingScore)); }
                        else
                            Console.WriteLine($"[HireAgent-Score] Loại {candidateId}: điểm {matchingScore:F1} < 50");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[HireAgent-Score] Lỗi chấm điểm {candidateId}: {ex.Message}");
                    }
                    finally { semaphore.Release(); }
                });

                await Task.WhenAll(tasks);

                // 4. Sort giảm dần, lấy top targetCount
                var sortedCandidates = candidateScores
                    .OrderByDescending(x => x.Score)
                    .Take(campaign.TargetCount)
                    .ToList();

                Console.WriteLine($"[HireAgent] Pool đạt chuẩn: {candidateScores.Count} → tiếp cận top {sortedCandidates.Count}");
                int invitedCount = 0;

                foreach (var item in sortedCandidates)
                {
                    if (currentConversations.Count + invitedCount >= campaign.TargetCount) break;

                    var resume = item.Resume;
                    var candidateId = resume.GetProperty("customerId").GetString()!;

                    string? cvText = null;
                    if (resume.TryGetProperty("extractedText", out var ext2) && ext2.ValueKind != JsonValueKind.Null)
                        cvText = ext2.GetString();
                    if (string.IsNullOrWhiteSpace(cvText)
                        && resume.TryGetProperty("contentJson", out var json2) && json2.ValueKind != JsonValueKind.Null)
                        cvText = json2.GetString();
                    if (string.IsNullOrWhiteSpace(cvText)) continue;

                    var recruiterMeta = await UserInfoHelper.GetRecruiterAndCompanyDetailsAsync(campaign.RecruiterId, _config);
                    var frontendUrl = _config["FrontendUrl"] ?? "http://localhost:5173";
                    var jobUrl = $"{frontendUrl.TrimEnd('/')}/jobs/{campaign.JobId}";

                    var chatPayload = new
                    {
                        job_description  = campaign.JobDescription,
                        cv_text          = cvText,
                        chat_history     = new List<object>(),
                        recruiter_name   = recruiterMeta.RecruiterName,
                        company_name     = recruiterMeta.CompanyName,
                        job_name         = campaign.JobName,
                        job_url          = jobUrl
                    };
                    var chatReq = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/cv/hire-agent/chat");
                    chatReq.Content = new StringContent(JsonSerializer.Serialize(chatPayload), Encoding.UTF8, "application/json");

                    try
                    {
                        var chatRes = await _httpClient.SendAsync(chatReq);
                        if (!chatRes.IsSuccessStatusCode) continue;

                        var chatDoc = JsonDocument.Parse(await chatRes.Content.ReadAsStringAsync());
                        var welcomeMsg = chatDoc.RootElement.GetProperty("reply").GetString()
                            ?? $"Chào bạn, tôi là trợ lý AI tuyển dụng của {campaign.JobName}. Tôi thấy hồ sơ của bạn rất ấn tượng và muốn trao đổi cơ hội làm việc!";

                        var chatMessageResponse = await _chatService.SendMessageAsync(campaign.RecruiterId, candidateId, welcomeMsg, "text");

                        var agentConv = new HireAgentConversation
                        {
                            Id             = Guid.NewGuid(),
                            CampaignId     = campaignId,
                            ConversationId = chatMessageResponse.ConversationId,
                            CandidateId    = candidateId,
                            CvText         = cvText,
                            Status         = "Screening",
                            MatchingScore  = item.Score,
                            LastQuestionAt = DateTimeOffset.UtcNow,
                            CreatedAt      = DateTimeOffset.UtcNow
                        };
                        await _hireAgentRepo.CreateConversationAsync(agentConv);

                        await _hubContext.Clients.Group(candidateId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);
                        await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("ReceiveMessage", chatMessageResponse);
                        invitedCount++;
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[HireAgent-Outreach] Lỗi tiếp cận ứng viên {candidateId}: {ex.Message}");
                    }
                }

                bool hasNewInvites = invitedCount > 0;
                if (currentConversations.Count + invitedCount >= campaign.TargetCount)
                    campaign.Status = "Completed";

                await _hireAgentRepo.UpdateCampaignAsync(campaign);

                await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("CampaignStatusChanged", new
                {
                    CampaignId = campaignId,
                    Status     = campaign.Status
                });

                if (hasNewInvites)
                    await _hubContext.Clients.Group(campaign.RecruiterId.ToLower()).SendAsync("CampaignConversationsUpdated", new
                    {
                        CampaignId = campaignId
                    });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgent] Lỗi trong tiến trình chiến dịch: {ex.Message}");
            }
        }
        finally
        {
            _runningCampaigns.TryRemove(campaignId, out _);
        }
    }
}

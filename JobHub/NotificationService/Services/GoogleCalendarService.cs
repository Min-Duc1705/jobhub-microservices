using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Services.Helpers;
using NotificationService.Services.Interface;

namespace NotificationService.Services;

public class GoogleCalendarService : IGoogleCalendarService
{
    private readonly NotificationDbContext _dbContext;
    private readonly IConfiguration _config;
    private static readonly HttpClient _httpClient = new HttpClient();

    public GoogleCalendarService(NotificationDbContext dbContext, IConfiguration config)
    {
        _dbContext = dbContext;
        _config = config;
    }

    private string ClientId => _config["Google:ClientId"] ?? _config["GoogleOAuth:ClientId"] ?? "YOUR_GOOGLE_CLIENT_ID";
    private string ClientSecret => _config["Google:ClientSecret"] ?? _config["GoogleOAuth:ClientSecret"] ?? "YOUR_GOOGLE_CLIENT_SECRET";
    
    private string RedirectUri
    {
        get
        {
            var configured = _config["Google:RedirectUri"] ?? _config["GoogleOAuth:RedirectUri"];
            if (!string.IsNullOrEmpty(configured)) return configured;
            
            // Auto fallback based on gateway or deployment URL
            var gatewayUrl = _config["GatewayUrl"] ?? "http://localhost:8080";
            return $"{gatewayUrl.TrimEnd('/')}/api/v1/google-calendar/callback";
        }
    }

    public string GetAuthUrl(string userId, string? origin = null)
    {
        var scope = Uri.EscapeDataString("https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email");
        var redirect = Uri.EscapeDataString(RedirectUri);
        var state = string.IsNullOrEmpty(origin) ? userId : $"{userId}|{origin}";
        return $"https://accounts.google.com/o/oauth2/v2/auth?client_id={ClientId}&redirect_uri={redirect}&response_type=code&scope={scope}&access_type=offline&prompt=consent&state={state}";
    }

    public async Task<UserGoogleCredential> ExchangeCodeForTokensAsync(string userId, string code)
    {
        var parameters = new Dictionary<string, string>
        {
            { "code", code },
            { "client_id", ClientId },
            { "client_secret", ClientSecret },
            { "redirect_uri", RedirectUri },
            { "grant_type", "authorization_code" }
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, "https://oauth2.googleapis.com/token")
        {
            Content = new FormUrlEncodedContent(parameters)
        };

        using var response = await _httpClient.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Lỗi trao đổi token Google: {error}");
        }

        var jsonStr = await response.Content.ReadAsStringAsync();
        using var jsonDoc = JsonDocument.Parse(jsonStr);
        var root = jsonDoc.RootElement;

        var accessToken = root.GetProperty("access_token").GetString() ?? "";
        // Refresh token chỉ được trả về ở lượt OAuth đầu tiên hoặc khi có prompt=consent
        var refreshToken = root.TryGetProperty("refresh_token", out var rtProp) ? rtProp.GetString() ?? "" : "";
        var expiresInSeconds = root.GetProperty("expires_in").GetInt32();
        var expiryTime = DateTimeOffset.UtcNow.AddSeconds(expiresInSeconds);

        // Lấy Email ứng với token
        var email = await FetchGoogleUserEmailAsync(accessToken);

        // Lưu hoặc cập nhật database
        var credential = await _dbContext.UserGoogleCredentials.FirstOrDefaultAsync(c => c.UserId == userId);
        if (credential == null)
        {
            credential = new UserGoogleCredential
            {
                Id = Guid.NewGuid(),
                UserId = userId,
                AccessToken = accessToken,
                RefreshToken = refreshToken,
                ExpiryTime = expiryTime,
                Email = email,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow
            };
            await _dbContext.UserGoogleCredentials.AddAsync(credential);
        }
        else
        {
            credential.AccessToken = accessToken;
            // Chỉ cập nhật refresh token nếu Google trả về refresh token mới
            if (!string.IsNullOrEmpty(refreshToken))
            {
                credential.RefreshToken = refreshToken;
            }
            credential.ExpiryTime = expiryTime;
            credential.Email = email;
            credential.UpdatedAt = DateTimeOffset.UtcNow;
            _dbContext.UserGoogleCredentials.Update(credential);
        }

        await _dbContext.SaveChangesAsync();
        return credential;
    }

    private async Task<string> FetchGoogleUserEmailAsync(string accessToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, "https://www.googleapis.com/oauth2/v3/userinfo");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

        using var response = await _httpClient.SendAsync(request);
        if (!response.IsSuccessStatusCode) return "unknown@google.com";

        var jsonStr = await response.Content.ReadAsStringAsync();
        using var jsonDoc = JsonDocument.Parse(jsonStr);
        if (jsonDoc.RootElement.TryGetProperty("email", out var emailProp))
        {
            return emailProp.GetString() ?? "unknown@google.com";
        }
        return "unknown@google.com";
    }

    private async Task<string> GetValidAccessTokenAsync(UserGoogleCredential credential)
    {
        // Nếu token còn hạn trên 5 phút, sử dụng trực tiếp
        if (credential.ExpiryTime > DateTimeOffset.UtcNow.AddMinutes(5))
        {
            return credential.AccessToken;
        }

        // Ngược lại, thực hiện refresh token
        if (string.IsNullOrEmpty(credential.RefreshToken))
        {
            throw new Exception("Không có refresh token để làm mới Google Access Token.");
        }

        var parameters = new Dictionary<string, string>
        {
            { "refresh_token", credential.RefreshToken },
            { "client_id", ClientId },
            { "client_secret", ClientSecret },
            { "grant_type", "refresh_token" }
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, "https://oauth2.googleapis.com/token")
        {
            Content = new FormUrlEncodedContent(parameters)
        };

        using var response = await _httpClient.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Lỗi refresh token Google: {error}");
        }

        var jsonStr = await response.Content.ReadAsStringAsync();
        using var jsonDoc = JsonDocument.Parse(jsonStr);
        var root = jsonDoc.RootElement;

        credential.AccessToken = root.GetProperty("access_token").GetString() ?? "";
        var expiresInSeconds = root.GetProperty("expires_in").GetInt32();
        credential.ExpiryTime = DateTimeOffset.UtcNow.AddSeconds(expiresInSeconds);
        credential.UpdatedAt = DateTimeOffset.UtcNow;

        _dbContext.UserGoogleCredentials.Update(credential);
        await _dbContext.SaveChangesAsync();

        return credential.AccessToken;
    }

    public async Task<bool> IsConnectedAsync(string userId)
    {
        var credential = await _dbContext.UserGoogleCredentials.FirstOrDefaultAsync(c => c.UserId == userId);
        return credential != null && !string.IsNullOrEmpty(credential.RefreshToken);
    }

    public async Task<string> GetConnectedEmailAsync(string userId)
    {
        var credential = await _dbContext.UserGoogleCredentials.FirstOrDefaultAsync(c => c.UserId == userId);
        return credential?.Email ?? string.Empty;
    }

    public async Task DisconnectAsync(string userId)
    {
        var credential = await _dbContext.UserGoogleCredentials.FirstOrDefaultAsync(c => c.UserId == userId);
        if (credential != null)
        {
            // Gửi yêu cầu thu hồi token lên Google (Best practices)
            try
            {
                var tokenToRevoke = !string.IsNullOrEmpty(credential.RefreshToken) ? credential.RefreshToken : credential.AccessToken;
                await _httpClient.PostAsync($"https://oauth2.googleapis.com/revoke?token={tokenToRevoke}", null);
            }
            catch {}

            _dbContext.UserGoogleCredentials.Remove(credential);
            await _dbContext.SaveChangesAsync();
        }
    }

    public async Task<string?> CreateEventAsync(
        string recruiterId, string title, string description, DateTimeOffset start, DateTimeOffset end, string candidateEmail)
    {
        var credential = await _dbContext.UserGoogleCredentials.FirstOrDefaultAsync(c => c.UserId == recruiterId);
        if (credential == null) return null;

        var accessToken = await GetValidAccessTokenAsync(credential);

        var eventPayload = new
        {
            summary = title,
            description = description,
            start = new { dateTime = start.ToString("yyyy-MM-ddTHH:mm:sszzz") },
            end = new { dateTime = end.ToString("yyyy-MM-ddTHH:mm:sszzz") },
            attendees = new[]
            {
                new { email = candidateEmail }
            }
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, "https://www.googleapis.com/calendar/v3/calendars/primary/events");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        request.Content = new StringContent(JsonSerializer.Serialize(eventPayload), Encoding.UTF8, "application/json");

        using var response = await _httpClient.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            Console.WriteLine($"[GoogleCalendar] Lỗi tạo lịch hẹn: {error}");
            return null;
        }

        var jsonStr = await response.Content.ReadAsStringAsync();
        using var jsonDoc = JsonDocument.Parse(jsonStr);
        
        // Trích xuất ID của sự kiện Google để lưu map
        if (jsonDoc.RootElement.TryGetProperty("id", out var idProp))
        {
            return idProp.GetString();
        }
        return null;
    }

    public async Task UpdateEventAsync(
        string recruiterId, string eventId, string title, string description, DateTimeOffset start, DateTimeOffset end, string candidateEmail)
    {
        var credential = await _dbContext.UserGoogleCredentials.FirstOrDefaultAsync(c => c.UserId == recruiterId);
        if (credential == null) return;

        var accessToken = await GetValidAccessTokenAsync(credential);

        var eventPayload = new
        {
            summary = title,
            description = description,
            start = new { dateTime = start.ToString("yyyy-MM-ddTHH:mm:sszzz") },
            end = new { dateTime = end.ToString("yyyy-MM-ddTHH:mm:sszzz") },
            attendees = new[]
            {
                new { email = candidateEmail }
            }
        };

        using var request = new HttpRequestMessage(HttpMethod.Put, $"https://www.googleapis.com/calendar/v3/calendars/primary/events/{eventId}");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        request.Content = new StringContent(JsonSerializer.Serialize(eventPayload), Encoding.UTF8, "application/json");

        using var response = await _httpClient.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            Console.WriteLine($"[GoogleCalendar] Lỗi cập nhật lịch hẹn {eventId}: {error}");
        }
    }

    public async Task DeleteEventAsync(string recruiterId, string eventId)
    {
        var credential = await _dbContext.UserGoogleCredentials.FirstOrDefaultAsync(c => c.UserId == recruiterId);
        if (credential == null) return;

        var accessToken = await GetValidAccessTokenAsync(credential);

        using var request = new HttpRequestMessage(HttpMethod.Delete, $"https://www.googleapis.com/calendar/v3/calendars/primary/events/{eventId}");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

        using var response = await _httpClient.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            Console.WriteLine($"[GoogleCalendar] Lỗi xóa lịch hẹn {eventId}: {error}");
        }
    }

    public async Task SyncAllExistingInterviewsAsync(string recruiterId)
    {
        // 1. Lấy tất cả chiến dịch của recruiterId
        var campaignMap = await _dbContext.HireAgentCampaigns
            .Where(c => c.RecruiterId == recruiterId)
            .ToDictionaryAsync(c => c.Id);

        if (campaignMap.Count == 0) return;

        // 2. Lấy các cuộc hội thoại tương ứng có lịch hẹn ở trạng thái Scheduled
        var conversations = await _dbContext.HireAgentConversations
            .Where(c => campaignMap.Keys.Contains(c.CampaignId) && c.Status == "Scheduled" && c.InterviewDate.HasValue)
            .ToListAsync();

        foreach (var conv in conversations)
        {
            try
            {
                // Kiểm tra xem đã map lịch Google chưa
                var exists = await _dbContext.InterviewGoogleEvents.AnyAsync(m => m.InterviewId == conv.Id);
                if (exists) continue;

                var campaign = campaignMap[conv.CampaignId];

                // Lấy thông tin ứng viên
                string candidateEmail = "candidate@jobhub.com";
                string candidateName = "Ứng viên";
                try
                {
                    var candidateInfo = await UserInfoHelper.GetUserDetailsAsync(conv.CandidateId, _config);
                    candidateEmail = candidateInfo.Email ?? candidateEmail;
                    candidateName = candidateInfo.FullName ?? candidateName;
                }
                catch {}

                var googleEventId = await CreateEventAsync(
                    recruiterId,
                    $"[JobHub] Lịch phỏng vấn: {candidateName}",
                    $"Lịch phỏng vấn vòng Final cho vị trí \"{campaign.JobName}\" (Chiến dịch AI Recruiter)",
                    conv.InterviewDate.Value,
                    conv.InterviewDate.Value.AddHours(1),
                    candidateEmail
                );

                if (!string.IsNullOrEmpty(googleEventId))
                {
                    var newMap = new InterviewGoogleEvent
                    {
                        Id = Guid.NewGuid(),
                        InterviewId = conv.Id,
                        GoogleEventId = googleEventId,
                        RecruiterId = recruiterId,
                        CreatedAt = DateTimeOffset.UtcNow
                    };
                    await _dbContext.InterviewGoogleEvents.AddAsync(newMap);
                    await _dbContext.SaveChangesAsync();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[GoogleCalendar-BulkSync] Lỗi đồng bộ cuộc hẹn campaign {conv.Id}: {ex.Message}");
            }
        }
    }
}

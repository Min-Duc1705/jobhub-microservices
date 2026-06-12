using Microsoft.Extensions.Configuration;
using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;

namespace NotificationService.Services.Helpers;

/// <summary>
/// Helper truy vấn thông tin người dùng (Profile, Email) từ các microservice nội bộ.
/// Dùng chung cho HireAgentService và các service khác cần lấy thông tin user.
/// </summary>
public static class UserInfoHelper
{
    private static readonly HttpClient _httpClient = new HttpClient();

    /// <summary>Lấy Email + FullName của một user (candidate hoặc recruiter) từ ProfileService + AuthService.</summary>
    public static async Task<(string? Email, string? FullName)> GetUserDetailsAsync(
        string userId, IConfiguration config)
    {
        try
        {
            var token = GenerateInternalToken(config);

            // 1. ProfileService → FullName + AppUserId
            var profileReq = new HttpRequestMessage(HttpMethod.Get, $"http://profileservice:8080/api/v1/customers/{userId}");
            profileReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var profileRes = await _httpClient.SendAsync(profileReq);
            if (!profileRes.IsSuccessStatusCode) return (null, null);

            var profileDoc = JsonDocument.Parse(await profileRes.Content.ReadAsStringAsync());
            var data = profileDoc.RootElement.GetProperty("data");

            var fullName  = data.TryGetProperty("fullName",  out var fn)  ? fn.GetString()  : null;
            var appUserId = data.TryGetProperty("appUserId", out var auid) ? auid.GetString() : null;

            if (string.IsNullOrEmpty(appUserId)) return (null, fullName);

            // 2. AuthService → Email
            var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{appUserId}");
            userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var userRes = await _httpClient.SendAsync(userReq);
            if (!userRes.IsSuccessStatusCode) return (null, fullName);

            var userDoc = JsonDocument.Parse(await userRes.Content.ReadAsStringAsync());
            var email = userDoc.RootElement.GetProperty("data").GetProperty("email").GetString();

            return (email, fullName);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[UserInfoHelper] Lỗi lấy thông tin user {userId}: {ex.Message}");
            return (null, null);
        }
    }

    /// <summary>
    /// Lấy RecruiterName + CompanyName + Email của HR từ ProfileService + CompanyService + AuthService.
    /// </summary>
    public static async Task<(string? RecruiterName, string? CompanyName, string? Email)> GetRecruiterAndCompanyDetailsAsync(
        string recruiterId, IConfiguration config)
    {
        try
        {
            var token = GenerateInternalToken(config);

            // 1. ProfileService → FullName + CompanyId + AppUserId
            var profileReq = new HttpRequestMessage(HttpMethod.Get, $"http://profileservice:8080/api/v1/customers/{recruiterId}");
            profileReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var profileRes = await _httpClient.SendAsync(profileReq);
            if (!profileRes.IsSuccessStatusCode) return (null, null, null);

            var profileDoc = JsonDocument.Parse(await profileRes.Content.ReadAsStringAsync());
            var data = profileDoc.RootElement.GetProperty("data");

            var recruiterName = data.TryGetProperty("fullName",  out var fn)   ? fn.GetString()   : null;
            var companyIdStr  = data.TryGetProperty("companyId", out var comp)  ? comp.GetString() : null;
            var appUserId     = data.TryGetProperty("appUserId", out var auid)  ? auid.GetString() : null;

            // 2. CompanyService → CompanyName
            string? compName = null;
            if (!string.IsNullOrEmpty(companyIdStr))
            {
                var compReq = new HttpRequestMessage(HttpMethod.Get, $"http://companyservice:8080/api/v1/companies/{companyIdStr}");
                compReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                var compRes = await _httpClient.SendAsync(compReq);
                if (compRes.IsSuccessStatusCode)
                {
                    var compDoc = JsonDocument.Parse(await compRes.Content.ReadAsStringAsync());
                    compName = compDoc.RootElement.GetProperty("data").GetProperty("name").GetString();
                }
            }

            // 3. AuthService → Email
            string? email = null;
            if (!string.IsNullOrEmpty(appUserId))
            {
                var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{appUserId}");
                userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                var userRes = await _httpClient.SendAsync(userReq);
                if (userRes.IsSuccessStatusCode)
                {
                    var userDoc = JsonDocument.Parse(await userRes.Content.ReadAsStringAsync());
                    email = userDoc.RootElement.GetProperty("data").GetProperty("email").GetString();
                }
            }

            return (recruiterName, compName, email);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[UserInfoHelper] Lỗi lấy thông tin recruiter {recruiterId}: {ex.Message}");
            return (null, null, null);
        }
    }

    private static string GenerateInternalToken(IConfiguration config)
    {
        var secretKey = config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
        var issuer    = config["Jwt:Issuer"]    ?? "JobHub";
        var audience  = config["Jwt:Audience"]  ?? "JobHubClient";
        return InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);
    }
}

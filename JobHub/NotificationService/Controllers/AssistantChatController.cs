using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using NotificationService.Data;
using NotificationService.Models.Response;
using NotificationService.Services;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Claims;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/assistant")]
[Authorize]
public class AssistantChatController : ControllerBase
{
    private readonly IChatService _chatService;
    private readonly NotificationDbContext _dbContext;
    private readonly IConfiguration _configuration;
    private static readonly HttpClient _httpClient = new HttpClient();

    public AssistantChatController(
        IChatService chatService,
        NotificationDbContext dbContext,
        IConfiguration configuration)
    {
        _chatService = chatService;
        _dbContext = dbContext;
        _configuration = configuration;
    }

    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không xác định được người dùng.");
        return Guid.Parse(sub);
    }

    [HttpPost("chat")]
    public async Task<IActionResult> Chat([FromBody] AssistantChatRequest request)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.Message))
        {
            return BadRequest(new { message = "Nội dung tin nhắn không được trống." });
        }

        try
        {
            var userId = GetCurrentUserId();

            // 1. Lưu tin nhắn của User vào DB thông qua IChatService
            // Tự động lấy hoặc tạo cuộc hội thoại giữa userId và "ai_assistant"
            var userMsg = await _chatService.SendMessageAsync(userId.ToString(), "ai_assistant", request.Message, "text");

            // 2. Lấy thông tin user hiện tại từ AuthService bằng token admin nội bộ
            var secretKey = _configuration["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
            var issuer = _configuration["Jwt:Issuer"] ?? "JobHub";
            var audience = _configuration["Jwt:Audience"] ?? "JobHubClient";
            var adminToken = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

            string email = "user@jobhub.com";
            string role = "USER";
            string username = "Người dùng";

            try
            {
                var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{userId}");
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
                Console.WriteLine($"[AssistantChatController] Lỗi khi lấy profile từ AuthService: {ex.Message}");
            }

            // 3. Tạo token đại diện cho User để gửi cho CVIntelligenceService
            var userToken = InternalTokenGenerator.GenerateTokenForUser(secretKey, issuer, audience, userId, email, role, username);

            // 4. Lấy lịch sử hội thoại thực tế từ DB để truyền làm context cho AI (lọc bỏ tin nhắn hiện tại)
            var dbMessages = await _dbContext.Messages
                .Where(m => m.ConversationId == userMsg.ConversationId && m.Id != userMsg.Id)
                .OrderByDescending(m => m.CreatedAt)
                .Take(15)
                .ToListAsync();

            dbMessages.Reverse();

            var history = dbMessages.Select(m => new AssistantMessageDto
            {
                Role = m.SenderId.Equals(userId.ToString(), StringComparison.OrdinalIgnoreCase) ? "user" : "model",
                Content = m.Content
            }).ToList();

            // 5. Build request gửi lên CVIntelligenceService
            var aiRequestPayload = new AssistantChatRequest
            {
                Message = request.Message,
                ImageBase64 = request.ImageBase64,
                FileContent = request.FileContent,
                ConversationHistory = history
            };

            var xSessionId = Request.Headers["X-Session-Id"].FirstOrDefault() ?? $"session_{userId}";

            var aiReq = new HttpRequestMessage(HttpMethod.Post, "http://cvintelligenceservice:5006/api/v1/assistant/chat");
            aiReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", userToken);
            aiReq.Headers.Add("X-Session-Id", xSessionId);
            
            var options = new JsonSerializerOptions { DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull };
            aiReq.Content = new StringContent(JsonSerializer.Serialize(aiRequestPayload, options), Encoding.UTF8, "application/json");

            var aiRes = await _httpClient.SendAsync(aiReq);

            if (!aiRes.IsSuccessStatusCode)
            {
                var errorBody = await aiRes.Content.ReadAsStringAsync();
                return StatusCode((int)aiRes.StatusCode, new { message = "Lỗi kết nối AI Assistant.", details = errorBody });
            }

            var aiContent = await aiRes.Content.ReadAsStringAsync();
            var aiResponse = JsonSerializer.Deserialize<AssistantChatResponse>(aiContent);

            if (aiResponse != null && !string.IsNullOrEmpty(aiResponse.Reply))
            {
                // 6. Lưu tin nhắn trả lời của AI vào DB
                await _chatService.SendMessageAsync("ai_assistant", userId.ToString(), aiResponse.Reply, "text");
            }

            return Ok(aiResponse);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[AssistantChatController] Lỗi: {ex.Message}");
            return StatusCode(500, new { message = "Lỗi hệ thống.", details = ex.Message });
        }
    }
}

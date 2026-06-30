using System;
using System.Security.Claims;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Services.Interface;
using Telegram.Bot;
using Telegram.Bot.Types;
using Microsoft.Extensions.Logging;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/telegram")]
public class TelegramWebhookController : ControllerBase
{
    private readonly ITelegramBotService _telegramBotService;
    private readonly NotificationDbContext _dbContext;
    private readonly IConfiguration _configuration;
    private readonly ILogger<TelegramWebhookController> _logger;

    private static readonly JsonSerializerOptions _jsonOptions = new JsonSerializerOptions
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        Converters = { 
            new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower),
            new UnixDateTimeConverter()
        }
    };

    public TelegramWebhookController(
        ITelegramBotService telegramBotService,
        NotificationDbContext dbContext,
        IConfiguration configuration,
        ILogger<TelegramWebhookController> logger)
    {
        _telegramBotService = telegramBotService;
        _dbContext = dbContext;
        _configuration = configuration;
        _logger = logger;
    }

    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User trong token.");
        return Guid.Parse(sub);
    }

    [HttpPost("webhook")]
    public async Task<IActionResult> HandleUpdate()
    {
        try
        {
            using var reader = new System.IO.StreamReader(Request.Body);
            var json = await reader.ReadToEndAsync();
            var update = JsonSerializer.Deserialize<Update>(json, _jsonOptions);
            if (update != null)
            {
                await _telegramBotService.ProcessUpdateAsync(update);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi giải mã webhook mặc định");
        }
        return Ok();
    }

    [HttpPost("webhook/{botToken}")]
    public async Task<IActionResult> HandleCustomBotUpdate([FromRoute] string botToken)
    {
        try
        {
            using var reader = new System.IO.StreamReader(Request.Body);
            var json = await reader.ReadToEndAsync();
            var update = JsonSerializer.Deserialize<Update>(json, _jsonOptions);
            if (update != null)
            {
                await _telegramBotService.ProcessUpdateAsync(update, botToken);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi giải mã webhook cho BotToken: {BotToken}", botToken);
        }
        return Ok();
    }

    [HttpGet("binding")]
    [Authorize]
    public async Task<IActionResult> GetBinding()
    {
        try
        {
            var userId = GetCurrentUserId();
            var binding = await _dbContext.UserTelegramBindings
                .FirstOrDefaultAsync(x => x.UserId == userId);

            var systemBotUsername = await _telegramBotService.GetSystemBotUsernameAsync();

            if (binding != null)
            {
                return Ok(new { 
                    isConnected = binding.TelegramChatId.HasValue, 
                    username = binding.Username,
                    botToken = binding.BotToken,
                    botUsername = binding.BotUsername ?? systemBotUsername
                });
            }
            return Ok(new { 
                isConnected = false,
                botUsername = systemBotUsername
            });
        }
        catch (Exception)
        {
            return Ok(new { isConnected = false });
        }
    }

    [HttpDelete("binding")]
    [Authorize]
    public async Task<IActionResult> DeleteBinding()
    {
        var userId = GetCurrentUserId();
        var binding = await _dbContext.UserTelegramBindings
            .FirstOrDefaultAsync(x => x.UserId == userId);

        if (binding != null)
        {
            _dbContext.UserTelegramBindings.Remove(binding);
            await _dbContext.SaveChangesAsync();
        }
        return Ok(new { success = true });
    }

    [HttpPost("binding/bot")]
    [Authorize]
    public async Task<IActionResult> BindCustomBot([FromBody] BindCustomBotRequest request)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.BotToken))
        {
            return BadRequest(new { message = "Bot Token không được trống." });
        }

        try
        {
            var userId = GetCurrentUserId();

            // 1. Kiểm tra Token Telegram
            var client = new TelegramBotClient(request.BotToken.Trim());
            var me = await client.GetMeAsync();

            if (me == null || string.IsNullOrEmpty(me.Username))
            {
                return BadRequest(new { message = "Bot Token không hợp lệ hoặc không phản hồi." });
            }

            // 2. Thiết lập Webhook động cho Bot này
            var gatewayUrl = _configuration["Telegram:WebhookDomain"] 
                          ?? _configuration["FrontendUrl"] 
                          ?? "http://localhost:5000"; 

            var webhookUrl = $"{gatewayUrl.TrimEnd('/')}/api/v1/telegram/webhook/{request.BotToken.Trim()}";
            
            await client.SetWebhookAsync(webhookUrl);

            // 3. Lưu thông tin vào database
            var binding = await _dbContext.UserTelegramBindings
                .FirstOrDefaultAsync(x => x.UserId == userId);

            if (binding != null)
            {
                binding.BotToken = request.BotToken.Trim();
                binding.BotUsername = me.Username;
                binding.TelegramChatId = null; 
                _dbContext.UserTelegramBindings.Update(binding);
            }
            else
            {
                binding = new UserTelegramBinding
                {
                    UserId = userId,
                    BotToken = request.BotToken.Trim(),
                    BotUsername = me.Username,
                    TelegramChatId = null
                };
                _dbContext.UserTelegramBindings.Add(binding);
            }

            await _dbContext.SaveChangesAsync();

            return Ok(new { 
                success = true, 
                botUsername = me.Username,
                botName = me.FirstName,
                message = "Kết nối Telegram Bot thành công! Hãy click liên kết để bắt đầu." 
            });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = $"Không thể kết nối Telegram Bot. Lỗi: {ex.Message}" });
        }
    }

    [HttpPost("subscriptions")]
    [Authorize]
    public async Task<IActionResult> Subscribe([FromBody] SubscribeRequest request)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.Type))
        {
            return BadRequest(new { message = "Loại subscription không hợp lệ." });
        }

        try
        {
            var userId = GetCurrentUserId();
            var binding = await _dbContext.UserTelegramBindings
                .FirstOrDefaultAsync(x => x.UserId == userId);

            if (binding == null)
            {
                return BadRequest(new { message = "Tài khoản của bạn chưa kết nối Telegram Bot." });
            }

            var interval = request.IntervalMinutes;
            if (request.Type.ToLower() != "reminder" && interval < 5 && interval > 0)
            {
                interval = 5;
            }

            var existingCount = await _dbContext.UserCronSchedules
                .CountAsync(s => s.UserId == userId && s.IsActive);
            if (existingCount >= 10)
            {
                return BadRequest(new { message = "Bạn đã có tối đa 10 lịch tự động đang chạy." });
            }

            var nextRun = (request.NextRunAt ?? DateTimeOffset.UtcNow.AddMinutes(interval <= 0 ? 5 : interval)).ToUniversalTime();

            var schedule = new UserCronSchedule
            {
                UserId          = userId,
                TelegramChatId  = binding.TelegramChatId ?? 0,
                BotToken        = binding.BotToken,
                Type            = request.Type.ToLower(),
                Keyword         = request.Keyword,
                IntervalMinutes = interval,
                IsActive        = true,
                CreatedAt       = DateTimeOffset.UtcNow,
                NextRunAt       = nextRun
            };

            _dbContext.UserCronSchedules.Add(schedule);
            await _dbContext.SaveChangesAsync();

            return Ok(new { 
                success = true, 
                id = schedule.Id, 
                type = schedule.Type,
                keyword = schedule.Keyword,
                intervalMinutes = schedule.IntervalMinutes 
            });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = $"Không thể tạo đặt lịch: {ex.Message}" });
        }
    }

    [HttpGet("subscriptions")]
    [Authorize]
    public async Task<IActionResult> GetSubscriptions()
    {
        try
        {
            var userId = GetCurrentUserId();
            var list = await _dbContext.UserCronSchedules
                .Where(x => x.UserId == userId)
                .OrderBy(x => x.Id)
                .ToListAsync();

            return Ok(new { success = true, data = list });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = $"Không thể lấy danh sách đặt lịch: {ex.Message}" });
        }
    }

    [HttpDelete("subscriptions/{id}")]
    [Authorize]
    public async Task<IActionResult> DeleteSubscription(int id)
    {
        try
        {
            var userId = GetCurrentUserId();
            var schedule = await _dbContext.UserCronSchedules
                .FirstOrDefaultAsync(x => x.Id == id && x.UserId == userId);

            if (schedule == null)
            {
                return NotFound(new { message = $"Không tìm thấy lịch #{id}." });
            }

            _dbContext.UserCronSchedules.Remove(schedule);
            await _dbContext.SaveChangesAsync();

            return Ok(new { success = true });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = $"Không thể xóa lịch: {ex.Message}" });
        }
    }

    [HttpPost("subscriptions/{id}/pause")]
    [Authorize]
    public async Task<IActionResult> PauseSubscription(int id)
    {
        try
        {
            var userId = GetCurrentUserId();
            var schedule = await _dbContext.UserCronSchedules
                .FirstOrDefaultAsync(x => x.Id == id && x.UserId == userId);

            if (schedule == null)
            {
                return NotFound(new { message = $"Không tìm thấy lịch #{id}." });
            }

            schedule.IsActive = false;
            await _dbContext.SaveChangesAsync();

            return Ok(new { success = true });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = $"Không thể tạm dừng lịch: {ex.Message}" });
        }
    }

    [HttpPost("subscriptions/{id}/resume")]
    [Authorize]
    public async Task<IActionResult> ResumeSubscription(int id)
    {
        try
        {
            var userId = GetCurrentUserId();
            var schedule = await _dbContext.UserCronSchedules
                .FirstOrDefaultAsync(x => x.Id == id && x.UserId == userId);

            if (schedule == null)
            {
                return NotFound(new { message = $"Không tìm thấy lịch #{id}." });
            }

            schedule.IsActive = true;
            schedule.NextRunAt = DateTimeOffset.UtcNow.AddMinutes(schedule.IntervalMinutes);
            await _dbContext.SaveChangesAsync();

            return Ok(new { success = true });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = $"Không thể tiếp tục lịch: {ex.Message}" });
        }
    }
}

public class BindCustomBotRequest
{
    public string BotToken { get; set; } = string.Empty;
}

public class SubscribeRequest
{
    public string Type { get; set; } = string.Empty;
    public string? Keyword { get; set; }
    public int IntervalMinutes { get; set; }
    public DateTimeOffset? NextRunAt { get; set; }
}

public class UnixDateTimeConverter : JsonConverter<DateTime>
{
    public override DateTime Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType == JsonTokenType.Number)
        {
            long unixTime = reader.GetInt64();
            return DateTimeOffset.FromUnixTimeSeconds(unixTime).UtcDateTime;
        }
        return reader.GetDateTime();
    }

    public override void Write(Utf8JsonWriter writer, DateTime value, JsonSerializerOptions options)
    {
        long unixTime = ((DateTimeOffset)value).ToUnixTimeSeconds();
        writer.WriteNumberValue(unixTime);
    }
}


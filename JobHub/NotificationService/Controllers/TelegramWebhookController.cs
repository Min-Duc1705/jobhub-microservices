using System;
using System.Security.Claims;
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
            var update = Newtonsoft.Json.JsonConvert.DeserializeObject<Update>(json);
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
            var update = Newtonsoft.Json.JsonConvert.DeserializeObject<Update>(json);
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

            if (binding != null)
            {
                return Ok(new { 
                    isConnected = binding.TelegramChatId.HasValue, 
                    username = binding.Username,
                    botToken = binding.BotToken,
                    botUsername = binding.BotUsername
                });
            }
            return Ok(new { isConnected = false });
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
}

public class BindCustomBotRequest
{
    public string BotToken { get; set; } = string.Empty;
}

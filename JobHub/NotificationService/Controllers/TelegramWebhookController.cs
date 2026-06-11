using System;
using System.Security.Claims;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using NotificationService.Data;
using NotificationService.Services.Interface;
using Telegram.Bot.Types;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/telegram")]
public class TelegramWebhookController : ControllerBase
{
    private readonly ITelegramBotService _telegramBotService;
    private readonly NotificationDbContext _dbContext;

    public TelegramWebhookController(
        ITelegramBotService telegramBotService,
        NotificationDbContext dbContext)
    {
        _telegramBotService = telegramBotService;
        _dbContext = dbContext;
    }

    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User trong token.");
        return Guid.Parse(sub);
    }

    [HttpPost("webhook")]
    public async Task<IActionResult> HandleUpdate([FromBody] Update update)
    {
        await _telegramBotService.ProcessUpdateAsync(update);
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
                return Ok(new { isConnected = true, username = binding.Username });
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
}

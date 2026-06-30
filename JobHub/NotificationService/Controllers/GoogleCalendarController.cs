using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using CommonService.Filters;
using Microsoft.Extensions.Configuration;
using NotificationService.Services.Interface;
using System;
using System.Security.Claims;
using System.Threading.Tasks;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/google-calendar")]
[Authorize]
public class GoogleCalendarController : ControllerBase
{
    private readonly IGoogleCalendarService _googleCalendarService;
    private readonly IConfiguration _config;

    public GoogleCalendarController(IGoogleCalendarService googleCalendarService, IConfiguration config)
    {
        _googleCalendarService = googleCalendarService;
        _config = config;
    }

    private string GetCurrentUserId()
    {
        return User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User.");
    }

    [HttpGet("auth-url")]
    [RequiresPermission("GET", "/api/v1/google-calendar/auth-url")]
    public IActionResult GetAuthUrl([FromQuery] string? origin = null)
    {
        try
        {
            var userId = GetCurrentUserId();
            var url = _googleCalendarService.GetAuthUrl(userId, origin);
            return Ok(new { url });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }

    [HttpGet("callback")]
    [AllowAnonymous]
    public async Task<IActionResult> Callback([FromQuery] string code, [FromQuery] string state)
    {
        string? origin = null;
        string userId = state;
        try
        {
            if (string.IsNullOrEmpty(code) || string.IsNullOrEmpty(state))
            {
                return BadRequest("Mã xác thực code hoặc state bị thiếu.");
            }

            // state chứa userId và có thể chứa origin phân tách bởi dấu |
            if (state.Contains('|'))
            {
                var parts = state.Split('|');
                userId = parts[0];
                origin = parts[1];
            }

            await _googleCalendarService.ExchangeCodeForTokensAsync(userId, code);

            // Chạy ngầm đồng bộ tất cả lịch hẹn cũ của chiến dịch tuyển dụng AI sang Google Calendar vừa liên kết
            var syncUserId = userId;
            _ = Task.Run(async () =>
            {
                try
                {
                    await _googleCalendarService.SyncAllExistingInterviewsAsync(syncUserId);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[GoogleCalendar-OAuth] Lỗi tự động đồng bộ sau OAuth: {ex.Message}");
                }
            });

            // Chuyển hướng người dùng quay trở lại giao diện Frontend
            var frontendUrl = !string.IsNullOrEmpty(origin) ? origin : (_config["FrontendUrl"] ?? "http://localhost:5173");
            return Redirect($"{frontendUrl.TrimEnd('/')}/hr/interview-scheduler?google_sync=success");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[GoogleCalendar-Callback] Lỗi callback: {ex.Message}");
            var frontendUrl = !string.IsNullOrEmpty(origin) ? origin : (_config["FrontendUrl"] ?? "http://localhost:5173");
            return Redirect($"{frontendUrl.TrimEnd('/')}/hr/interview-scheduler?google_sync=failed&error={Uri.EscapeDataString(ex.Message)}");
        }
    }

    [HttpGet("status")]
    [RequiresPermission("GET", "/api/v1/google-calendar/status")]
    public async Task<IActionResult> GetStatus()
    {
        try
        {
            var userId = GetCurrentUserId();
            var isConnected = await _googleCalendarService.IsConnectedAsync(userId);
            var email = isConnected ? await _googleCalendarService.GetConnectedEmailAsync(userId) : string.Empty;
            return Ok(new { isConnected, email });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }

    [HttpPost("disconnect")]
    [RequiresPermission("POST", "/api/v1/google-calendar/disconnect")]
    public async Task<IActionResult> Disconnect()
    {
        try
        {
            var userId = GetCurrentUserId();
            await _googleCalendarService.DisconnectAsync(userId);
            return Ok(new { message = "Đã hủy liên kết Google Calendar thành công." });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }

    [HttpPost("sync-existing")]
    [RequiresPermission("POST", "/api/v1/google-calendar/sync-existing")]
    public async Task<IActionResult> SyncExisting()
    {
        try
        {
            var userId = GetCurrentUserId();
            var isConnected = await _googleCalendarService.IsConnectedAsync(userId);
            if (!isConnected)
            {
                return BadRequest(new { message = "Tài khoản Google Calendar chưa được liên kết." });
            }

            await _googleCalendarService.SyncAllExistingInterviewsAsync(userId);
            return Ok(new { message = "Đồng bộ lịch cũ thành công." });
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }
}

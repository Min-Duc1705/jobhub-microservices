using CommonService.Annotations;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NotificationService.Models.Response;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Security.Claims;
using System.Threading.Tasks;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/notifications")]
[Authorize]
public class NotificationsController : ControllerBase
{
    private readonly INotificationService _notificationService;

    public NotificationsController(INotificationService notificationService)
    {
        _notificationService = notificationService;
    }

    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User trong token.");
        return Guid.Parse(sub);
    }

    // GET /api/v1/notifications
    [HttpGet]
    [ApiMessage("Lấy danh sách thông báo thành công")]
    public async Task<ActionResult<List<NotificationResponse>>> GetNotifications()
    {
        var userId = GetCurrentUserId();
        var result = await _notificationService.GetUserNotificationsAsync(userId);
        return Ok(result);
    }

    // PATCH /api/v1/notifications/{id}/read
    [HttpPatch("{id:guid}/read")]
    [ApiMessage("Đánh dấu đã đọc thông báo thành công")]
    public async Task<ActionResult<NotificationResponse>> MarkAsRead(Guid id)
    {
        var userId = GetCurrentUserId();
        var result = await _notificationService.MarkAsReadAsync(id, userId);
        return Ok(result);
    }

    // PATCH /api/v1/notifications/read-all
    [HttpPatch("read-all")]
    [ApiMessage("Đánh dấu đã đọc tất cả thông báo thành công")]
    public async Task<IActionResult> MarkAllAsRead()
    {
        var userId = GetCurrentUserId();
        await _notificationService.MarkAllAsReadAsync(userId);
        return Ok(new { success = true });
    }
}

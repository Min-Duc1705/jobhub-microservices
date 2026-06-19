using System;

namespace NotificationService.Models;

/// <summary>
/// Lịch cron do người dùng tạo qua lệnh Telegram /subscribe.
/// Mỗi bản ghi tương ứng một lịch tự động gửi thông báo theo chu kỳ.
/// </summary>
public class UserCronSchedule
{
    public int Id { get; set; }

    /// <summary>JobHub UserId</summary>
    public Guid UserId { get; set; }

    /// <summary>Telegram Chat ID để gửi kết quả</summary>
    public long TelegramChatId { get; set; }

    /// <summary>Bot token tương ứng (null = system bot)</summary>
    public string? BotToken { get; set; }

    /// <summary>
    /// Loại thông báo: "jobs" | "applications" | "notifications" | "interviews" | "campaigns"
    /// </summary>
    public string Type { get; set; } = string.Empty;

    /// <summary>Từ khoá lọc (chỉ dùng cho type=jobs). Null = tất cả job.</summary>
    public string? Keyword { get; set; }

    /// <summary>Chu kỳ thực thi tính bằng phút (15, 30, 60, 120, 240, 360, 720, 1440)</summary>
    public int IntervalMinutes { get; set; }

    /// <summary>Đang hoạt động hay đã tạm dừng</summary>
    public bool IsActive { get; set; } = true;

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    /// <summary>Lần cuối cùng thực thi (dùng để lọc job mới)</summary>
    public DateTimeOffset? LastRunAt { get; set; }

    /// <summary>Lần kế tiếp sẽ thực thi</summary>
    public DateTimeOffset NextRunAt { get; set; }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using NotificationService.Models;
using Telegram.Bot;

namespace NotificationService.Services;

public partial class TelegramBotService
{
    // Các interval hợp lệ (phút)
    private static readonly Dictionary<string, int> _validIntervals = new()
    {
        ["15m"] = 15, ["30m"] = 30,
        ["1h"]  = 60, ["2h"]  = 120, ["4h"] = 240,
        ["6h"]  = 360, ["12h"] = 720, ["24h"] = 1440
    };

    /// <summary>
    /// /subscribe jobs [keyword] every 1h
    /// /subscribe notifications every 30m
    /// /subscribe applications every 1h
    /// /subscribe interviews every 6h
    /// /subscribe campaigns every 2h
    /// </summary>
    private async Task HandleSubscribeCommandAsync(long chatId, Guid userId, string text, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        // Giới hạn tối đa 5 lịch mỗi user
        var existingCount = await _dbContext.UserCronSchedules
            .CountAsync(s => s.UserId == userId && s.IsActive);
        if (existingCount >= 5)
        {
            await activeClient.SendTextMessageAsync(chatId,
                "⚠️ Bạn đã có tối đa *5 lịch tự động* đang chạy.\n\nDùng `/list` để xem và `/delete <id>` để xoá bớt trước khi thêm mới.",
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        // Parse: /subscribe <type> [keyword] every <interval>
        var parts = text.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);

        if (parts.Length < 4)
        {
            await activeClient.SendTextMessageAsync(chatId,
                "❌ Cú pháp không hợp lệ. Ví dụ:\n" +
                "`/subscribe jobs react every 1h`\n" +
                "`/subscribe notifications every 30m`\n\n" +
                "Dùng `/help` để xem hướng dẫn đầy đủ.",
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        var type = parts[1].ToLower();
        var validTypes = new[] { "jobs", "notifications", "applications", "interviews", "campaigns" };
        if (!validTypes.Contains(type))
        {
            await activeClient.SendTextMessageAsync(chatId,
                $"❌ Loại lịch `{type}` không hợp lệ.\n\nLoại hỗ trợ: `jobs` · `notifications` · `applications` · `interviews` · `campaigns`",
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        var intervalStr = parts[^1].ToLower();
        int intervalMinutes = 0;
        if (!_validIntervals.TryGetValue(intervalStr, out intervalMinutes))
        {
            var match = System.Text.RegularExpressions.Regex.Match(intervalStr, @"^(\d+)(m|h)$");
            if (match.Success)
            {
                int val = int.Parse(match.Groups[1].Value);
                string unit = match.Groups[2].Value;
                intervalMinutes = unit == "m" ? val : val * 60;
            }
        }

        if (intervalMinutes < 5)
        {
            await activeClient.SendTextMessageAsync(chatId,
                $"❌ Chu kỳ `{intervalStr}` không hợp lệ hoặc quá ngắn.\n\n⚠️ Hệ thống hỗ trợ chu kỳ tùy chọn từ *5 phút trở lên* (ví dụ: `5m`, `10m`, `30m`, `1h`, `2h`, v.v.).",
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        // Xác định keyword (chỉ cho type=jobs)
        string? keyword = null;
        if (type == "jobs" && parts.Length > 4 && parts[^2].ToLower() == "every")
        {
            // Lấy keyword giữa type và "every"
            keyword = string.Join(" ", parts[2..^2]).Trim();
            if (string.IsNullOrWhiteSpace(keyword)) keyword = null;
        }

        var schedule = new UserCronSchedule
        {
            UserId          = userId,
            TelegramChatId  = chatId,
            BotToken        = botToken,
            Type            = type,
            Keyword         = keyword,
            IntervalMinutes = intervalMinutes,
            IsActive        = true,
            CreatedAt       = DateTimeOffset.UtcNow,
            NextRunAt       = DateTimeOffset.UtcNow.AddMinutes(intervalMinutes)
        };

        _dbContext.UserCronSchedules.Add(schedule);
        await _dbContext.SaveChangesAsync();

        var keywordText = keyword != null ? $" theo keyword *{keyword}*" : "";
        var intervalText = CronSchedulerWorker.FormatInterval(intervalMinutes);

        await activeClient.SendTextMessageAsync(chatId,
            $"✅ *Đã đặt lịch #{schedule.Id} thành công!*\n\n" +
            $"📌 Loại: `{type}`{keywordText}\n" +
            $"⏰ Chu kỳ: mỗi *{intervalText}*\n" +
            $"🕐 Lần đầu gửi: {schedule.NextRunAt.ToOffset(TimeSpan.FromHours(7)):dd/MM HH:mm} (ICT)\n\n" +
            $"Dùng `/pause {schedule.Id}` để tạm dừng hoặc `/delete {schedule.Id}` để xoá.",
            parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    /// <summary>/list — Liệt kê các lịch đang có của user</summary>
    private async Task HandleListCommandAsync(long chatId, Guid userId, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        var schedules = await _dbContext.UserCronSchedules
            .Where(s => s.UserId == userId)
            .OrderBy(s => s.Id)
            .ToListAsync();

        if (!schedules.Any())
        {
            await activeClient.SendTextMessageAsync(chatId,
                "📋 Bạn chưa có lịch tự động nào.\n\nDùng `/subscribe` để tạo lịch đầu tiên!",
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        var sb = new StringBuilder();
        sb.AppendLine($"📋 *Danh sách lịch tự động của bạn ({schedules.Count})*\n");

        foreach (var s in schedules)
        {
            var status    = s.IsActive ? "🟢 Đang chạy" : "🔴 Tạm dừng";
            var keyword   = s.Keyword != null ? $" · keyword: `{s.Keyword}`" : "";
            var nextRun   = s.NextRunAt.ToOffset(TimeSpan.FromHours(7)).ToString("dd/MM HH:mm");
            var lastRun   = s.LastRunAt.HasValue ? s.LastRunAt.Value.ToOffset(TimeSpan.FromHours(7)).ToString("dd/MM HH:mm") : "Chưa chạy";
            var interval  = CronSchedulerWorker.FormatInterval(s.IntervalMinutes);

            sb.AppendLine($"*#{s.Id}* · `{s.Type}`{keyword}");
            sb.AppendLine($"   {status} · mỗi {interval}");
            sb.AppendLine($"   Lần cuối: {lastRun} → Kế tiếp: {nextRun}");
            if (s.IsActive)
                sb.AppendLine($"   /pause {s.Id} · /delete {s.Id}");
            else
                sb.AppendLine($"   /resume {s.Id} · /delete {s.Id}");
            sb.AppendLine();
        }

        await activeClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    /// <summary>/pause <id></summary>
    private async Task HandlePauseCommandAsync(long chatId, Guid userId, string text, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        if (!TryParseScheduleId(text, out int id))
        {
            await activeClient.SendTextMessageAsync(chatId, "❌ Cú pháp: `/pause <id>`. Ví dụ: `/pause 3`", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        var schedule = await _dbContext.UserCronSchedules.FirstOrDefaultAsync(s => s.Id == id && s.UserId == userId);
        if (schedule == null)
        {
            await activeClient.SendTextMessageAsync(chatId, $"❌ Không tìm thấy lịch #{id} thuộc tài khoản của bạn.");
            return;
        }

        if (!schedule.IsActive)
        {
            await activeClient.SendTextMessageAsync(chatId, $"ℹ️ Lịch #{id} đã ở trạng thái tạm dừng rồi.");
            return;
        }

        schedule.IsActive = false;
        await _dbContext.SaveChangesAsync();
        await activeClient.SendTextMessageAsync(chatId, $"⏸ *Lịch #{id} đã tạm dừng.*\n\nDùng `/resume {id}` để tiếp tục.", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    /// <summary>/resume <id></summary>
    private async Task HandleResumeCommandAsync(long chatId, Guid userId, string text, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        if (!TryParseScheduleId(text, out int id))
        {
            await activeClient.SendTextMessageAsync(chatId, "❌ Cú pháp: `/resume <id>`. Ví dụ: `/resume 3`", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        var schedule = await _dbContext.UserCronSchedules.FirstOrDefaultAsync(s => s.Id == id && s.UserId == userId);
        if (schedule == null)
        {
            await activeClient.SendTextMessageAsync(chatId, $"❌ Không tìm thấy lịch #{id} thuộc tài khoản của bạn.");
            return;
        }

        if (schedule.IsActive)
        {
            await activeClient.SendTextMessageAsync(chatId, $"ℹ️ Lịch #{id} đang chạy bình thường rồi.");
            return;
        }

        schedule.IsActive = true;
        schedule.NextRunAt = DateTimeOffset.UtcNow.AddMinutes(schedule.IntervalMinutes);
        await _dbContext.SaveChangesAsync();
        await activeClient.SendTextMessageAsync(chatId,
            $"▶️ *Lịch #{id} đã tiếp tục.*\n\nLần gửi tiếp theo: {schedule.NextRunAt.ToOffset(TimeSpan.FromHours(7)):dd/MM HH:mm} (ICT)",
            parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    /// <summary>/delete <id></summary>
    private async Task HandleDeleteCommandAsync(long chatId, Guid userId, string text, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        if (!TryParseScheduleId(text, out int id))
        {
            await activeClient.SendTextMessageAsync(chatId, "❌ Cú pháp: `/delete <id>`. Ví dụ: `/delete 3`", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        var schedule = await _dbContext.UserCronSchedules.FirstOrDefaultAsync(s => s.Id == id && s.UserId == userId);
        if (schedule == null)
        {
            await activeClient.SendTextMessageAsync(chatId, $"❌ Không tìm thấy lịch #{id} thuộc tài khoản của bạn.");
            return;
        }

        _dbContext.UserCronSchedules.Remove(schedule);
        await _dbContext.SaveChangesAsync();
        await activeClient.SendTextMessageAsync(chatId, $"🗑 *Lịch #{id} đã được xoá.*", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private static bool TryParseScheduleId(string text, out int id)
    {
        id = 0;
        var parts = text.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
        return parts.Length >= 2 && int.TryParse(parts[1], out id);
    }

    private bool TryParseNaturalScheduleIntent(string text, out string? type, out string? keyword, out int intervalMinutes)
    {
        type = null;
        keyword = null;
        intervalMinutes = 0;

        var lowerText = text.ToLower().Trim();

        // Check if the message indicates a schedule intent
        bool hasScheduleIndicator = lowerText.Contains("đặt lịch") ||
                                    lowerText.Contains("nhắc nhở") ||
                                    lowerText.Contains("gửi cho tôi") ||
                                    lowerText.Contains("subscribe") ||
                                    lowerText.Contains("đăng ký") ||
                                    lowerText.Contains("cứ") ||
                                    lowerText.Contains("mỗi") ||
                                    lowerText.Contains("every");

        if (!hasScheduleIndicator)
        {
            return false;
        }

        // Extract Interval
        int parsedInterval = 0;
        bool foundInterval = false;

        // Match: (cứ|mỗi|every|sau)\s*(\d+)\s*(phút|ph|p|giờ|tiếng|h|m|min)
        var matchInterval = System.Text.RegularExpressions.Regex.Match(lowerText, @"(?:cứ|mỗi|every|sau)\s*(\d+)\s*(phút|ph|p|giờ|tiếng|h|m|min|s|second|minute|hour)");
        if (matchInterval.Success)
        {
            int val = int.Parse(matchInterval.Groups[1].Value);
            string unit = matchInterval.Groups[2].Value;

            if (unit.StartsWith("phút") || unit.StartsWith("m") || unit.StartsWith("min") || unit == "p" || unit == "ph")
            {
                parsedInterval = val;
            }
            else if (unit.StartsWith("giờ") || unit.StartsWith("tiếng") || unit.StartsWith("h") || unit.StartsWith("hour"))
            {
                parsedInterval = val * 60;
            }
            foundInterval = true;
        }
        else
        {
            // Check for shorthand like "1h", "30m", "15m" directly
            var matchShort = System.Text.RegularExpressions.Regex.Match(lowerText, @"\b(\d+)\s*(h|m|min|phút|ph|p|giờ)\b");
            if (matchShort.Success)
            {
                int val = int.Parse(matchShort.Groups[1].Value);
                string unit = matchShort.Groups[2].Value;

                if (unit.StartsWith("phút") || unit.StartsWith("m") || unit.StartsWith("min") || unit == "p" || unit == "ph")
                {
                    parsedInterval = val;
                }
                else if (unit.StartsWith("giờ") || unit.StartsWith("tiếng") || unit.StartsWith("h"))
                {
                    parsedInterval = val * 60;
                }
                foundInterval = true;
            }
            else if (lowerText.Contains("mỗi giờ") || lowerText.Contains("hằng giờ") || lowerText.Contains("hàng giờ") || lowerText.Contains("mỗi tiếng") || lowerText.Contains("hằng tiếng"))
            {
                parsedInterval = 60;
                foundInterval = true;
            }
            else if (lowerText.Contains("mỗi ngày") || lowerText.Contains("hằng ngày") || lowerText.Contains("hàng ngày"))
            {
                parsedInterval = 1440;
                foundInterval = true;
            }
        }

        // Determine Type
        type = "jobs"; // Default to jobs
        
        if (lowerText.Contains("ứng viên") || lowerText.Contains("hồ sơ") || lowerText.Contains("ứng tuyển") || lowerText.Contains("cv") || lowerText.Contains("application"))
        {
            type = "applications";
        }
        else if (lowerText.Contains("phỏng vấn") || lowerText.Contains("lịch hẹn") || lowerText.Contains("interview"))
        {
            type = "interviews";
        }
        else if (lowerText.Contains("chiến dịch") || lowerText.Contains("campaign"))
        {
            type = "campaigns";
        }
        else if (lowerText.Contains("thông báo") && !lowerText.Contains("job") && !lowerText.Contains("việc làm") && !lowerText.Contains("tuyển"))
        {
            type = "notifications";
        }

        // Extract Keyword (only for type="jobs")
        if (type == "jobs")
        {
            var matchKeyword = System.Text.RegularExpressions.Regex.Match(lowerText, @"(?:job|việc làm|tuyển dụng|tuyển|keyword|từ khóa)\s+([a-zA-Z0-9#+\.\s\-]+?)(?:\s+(?:mới|mới nhất|cứ|mỗi|mọi|every|sau|cho tôi|hằng|hàng|$))");
            if (matchKeyword.Success)
            {
                keyword = matchKeyword.Groups[1].Value.Trim();
            }
            else
            {
                var temp = lowerText;
                var stopWords = new[] {
                    "tôi muốn", "muốn", "thông báo", "cho tôi", "gửi cho tôi", "đăng ký", "subscribe", 
                    "mới nhất", "mới", "cứ", "mỗi", "hằng", "hàng", "every", "sau", "tuyển dụng", "tuyển", 
                    "việc làm", "job", "jobs", "phút", "giờ", "tiếng", "h", "m", "ngày", "lịch"
                };
                foreach (var sw in stopWords)
                {
                    temp = temp.Replace(sw, "");
                }
                
                temp = System.Text.RegularExpressions.Regex.Replace(temp, @"[^\w\s#+-]", " ");
                temp = System.Text.RegularExpressions.Regex.Replace(temp, @"\s+", " ").Trim();
                
                if (!string.IsNullOrEmpty(temp) && temp.Length < 30)
                {
                    keyword = temp;
                }
            }

            if (!string.IsNullOrEmpty(keyword))
            {
                keyword = keyword.Trim();
            }
        }

        intervalMinutes = parsedInterval;

        // Chỉ chấp nhận là đặt lịch tự động khi:
        // 1. Có chu kỳ rõ ràng (ví dụ: foundInterval = true)
        // 2. HOẶC có hành động đăng ký/subscribe/đặt lịch chủ động đi kèm các loại dữ liệu cụ thể
        bool hasExplicitSubscribe = lowerText.Contains("đăng ký") || 
                                    lowerText.Contains("subscribe") || 
                                    lowerText.Contains("đặt lịch");

        return foundInterval || (hasExplicitSubscribe && (lowerText.Contains("notification") || lowerText.Contains("thông báo") || lowerText.Contains("job") || lowerText.Contains("việc làm")));
    }

    private async Task HandleNaturalScheduleAsync(long chatId, Guid userId, string type, string? keyword, int intervalMinutes, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        var existingCount = await _dbContext.UserCronSchedules
            .CountAsync(s => s.UserId == userId && s.IsActive);
        if (existingCount >= 5)
        {
            await activeClient.SendTextMessageAsync(chatId,
                "⚠️ Bạn đã có tối đa *5 lịch tự động* đang chạy.\n\nDùng `/list` để xem và `/delete <id>` để xoá bớt trước khi thêm mới.",
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        int finalInterval = 60; // Default to 1h
        var note = "";
        if (intervalMinutes > 0)
        {
            if (intervalMinutes < 5)
            {
                finalInterval = 5;
                note = $"\n\n_(Lưu ý: Hệ thống đã đặt chu kỳ tối thiểu là **5 phút** thay vì {intervalMinutes} phút do giới hạn hệ thống.)_";
            }
            else
            {
                finalInterval = intervalMinutes;
            }
        }
        else
        {
            note = "\n\n_(Tôi đã đặt chu kỳ mặc định là **1 giờ** vì chưa nhận rõ khoảng thời gian. Bạn có thể thay đổi bằng lệnh `/subscribe` hoặc xóa đi đặt lại.)_";
        }

        var schedule = new UserCronSchedule
        {
            UserId          = userId,
            TelegramChatId  = chatId,
            BotToken        = botToken,
            Type            = type,
            Keyword         = keyword,
            IntervalMinutes = finalInterval,
            IsActive        = true,
            CreatedAt       = DateTimeOffset.UtcNow,
            NextRunAt       = DateTimeOffset.UtcNow.AddMinutes(finalInterval)
        };

        _dbContext.UserCronSchedules.Add(schedule);
        await _dbContext.SaveChangesAsync();

        var keywordText = keyword != null ? $" theo keyword *{keyword}*" : "";
        var intervalText = CronSchedulerWorker.FormatInterval(finalInterval);

        await activeClient.SendTextMessageAsync(chatId,
            $"🎯 *Đã tự động đặt lịch #{schedule.Id} thành công!*\n\n" +
            $"📌 Loại: `{type}`{keywordText}\n" +
            $"⏰ Chu kỳ: mỗi *{intervalText}*\n" +
            $"🕐 Lần đầu gửi: {schedule.NextRunAt.ToOffset(TimeSpan.FromHours(7)):dd/MM HH:mm} (ICT){note}\n\n" +
            $"💡 Bạn có thể quản lý lịch bằng các lệnh:\n" +
            $"• `/list` - Xem tất cả lịch\n" +
            $"• `/pause {schedule.Id}` - Tạm dừng\n" +
            $"• `/delete {schedule.Id}` - Xoá lịch",
            parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }
}

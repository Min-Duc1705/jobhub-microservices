using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Services.Interface;
using Telegram.Bot;
using Telegram.Bot.Types;

namespace NotificationService.Services;

public class TelegramBotService : ITelegramBotService
{
    private readonly TelegramBotClient? _botClient;
    private readonly NotificationDbContext _dbContext;
    private readonly ILogger<TelegramBotService> _logger;

    public TelegramBotService(
        IConfiguration configuration,
        NotificationDbContext dbContext,
        ILogger<TelegramBotService> logger)
    {
        _dbContext = dbContext;
        _logger = logger;

        var token = configuration["Telegram:BotToken"];
        if (!string.IsNullOrEmpty(token) && token != "YOUR_TELEGRAM_BOT_TOKEN")
        {
            _botClient = new TelegramBotClient(token);
        }
        else
        {
            _logger.LogWarning("Telegram Bot Token is not configured. Telegram bot services will be disabled.");
        }
    }

    public async Task ProcessUpdateAsync(Update update)
    {
        if (_botClient == null || update.Message == null || string.IsNullOrEmpty(update.Message.Text))
            return;

        var message = update.Message;
        var chatId = message.Chat.Id;
        var text = message.Text.Trim();
        var username = message.Chat.Username;

        try
        {
            if (text.StartsWith("/start"))
            {
                await HandleStartCommandAsync(chatId, text, username);
            }
            else
            {
                // Check if user is bound
                var binding = await _dbContext.UserTelegramBindings
                    .FirstOrDefaultAsync(x => x.TelegramChatId == chatId);

                if (binding == null)
                {
                    await _botClient.SendTextMessageAsync(chatId,
                        "⚠️ Tài khoản của bạn chưa được liên kết với JobHub.\n\n" +
                        "Vui lòng truy cập trang *Cài đặt cá nhân* trên website JobHub và nhấn nút *Kết nối Telegram* để thực hiện liên kết.",
                        parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                    return;
                }

                if (text.StartsWith("/help"))
                {
                    await HandleHelpCommandAsync(chatId);
                }
                else if (text.StartsWith("/campaigns"))
                {
                    await HandleCampaignsCommandAsync(chatId, binding.UserId);
                }
                else if (text.StartsWith("/interviews"))
                {
                    await HandleInterviewsCommandAsync(chatId, binding.UserId);
                }
                else if (text.StartsWith("/notifications"))
                {
                    await HandleNotificationsCommandAsync(chatId, binding.UserId);
                }
                else if (text.StartsWith("/profile"))
                {
                    await HandleProfileCommandAsync(chatId, binding.UserId, binding);
                }
                else
                {
                    await _botClient.SendTextMessageAsync(chatId,
                        "🤖 Xin chào! Tôi là trợ lý JobHub.\n" +
                        "Tôi không hiểu lệnh này. Gõ `/help` để xem danh sách các lệnh hỗ trợ.",
                        parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi xử lý Telegram update cho ChatId: {ChatId}", chatId);
        }
    }

    public async Task SendPushNotificationAsync(Guid userId, string title, string message)
    {
        if (_botClient == null) return;

        try
        {
            var binding = await _dbContext.UserTelegramBindings
                .FirstOrDefaultAsync(x => x.UserId == userId);

            if (binding != null)
            {
                var formatted = $"🔔 *{title}*\n\n{message}";
                await _botClient.SendTextMessageAsync(binding.TelegramChatId, formatted, parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi gửi thông báo đẩy qua Telegram cho User {UserId}", userId);
        }
    }

    private async Task HandleStartCommandAsync(long chatId, string text, string? username)
    {
        if (_botClient == null) return;

        // Check deep link binding parameter /start BIND_UserId
        var parts = text.Split(' ');
        if (parts.Length > 1 && parts[1].StartsWith("BIND_"))
        {
            var userIdStr = parts[1].Substring(5);
            if (Guid.TryParse(userIdStr, out Guid userId))
            {
                var existing = await _dbContext.UserTelegramBindings
                    .FirstOrDefaultAsync(x => x.UserId == userId || x.TelegramChatId == chatId);

                if (existing != null)
                {
                    existing.TelegramChatId = chatId;
                    existing.Username = username;
                    existing.CreatedDate = DateTimeOffset.UtcNow;
                    _dbContext.UserTelegramBindings.Update(existing);
                }
                else
                {
                    var binding = new UserTelegramBinding
                    {
                        UserId = userId,
                        TelegramChatId = chatId,
                        Username = username
                    };
                    _dbContext.UserTelegramBindings.Add(binding);
                }

                await _dbContext.SaveChangesAsync();

                await _botClient.SendTextMessageAsync(chatId,
                    "🎉 *Liên kết thành công!*\n\n" +
                    "Tài khoản của bạn đã được kết nối với JobHub. Từ bây giờ bạn sẽ nhận được thông báo đẩy trực tiếp qua Telegram này.\n\n" +
                    "Gõ `/help` để xem danh sách lệnh hỗ trợ.",
                    parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                    
                // Gửi thông báo test ngay lập tức
                await _botClient.SendTextMessageAsync(chatId,
                    "🔔 *Kiểm tra kết nối*\n\nChào mừng bạn! Hệ thống thông báo tự động JobHub đã hoạt động tốt trên thiết bị của bạn.",
                    parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                return;
            }
        }

        await _botClient.SendTextMessageAsync(chatId,
            "👋 Chào mừng bạn đến với *JobHub Bot*!\n\n" +
            "Để nhận thông báo đẩy và sử dụng các tính năng điều khiển, vui lòng vào trang *Cài đặt cá nhân* của JobHub trên trình duyệt web và click nút *Kết nối Telegram*.",
            parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleHelpCommandAsync(long chatId)
    {
        if (_botClient == null) return;

        var msg = "🤖 *Danh sách lệnh hỗ trợ trên JobHub Bot*:\n\n" +
                  "📌 `/profile` - Xem thông tin tài khoản liên kết hiện tại\n" +
                  "📌 `/notifications` - Xem 5 thông báo chưa đọc mới nhất\n" +
                  "📌 `/campaigns` - (Dành cho HR) Xem danh sách chiến dịch tuyển dụng AI\n" +
                  "📌 `/interviews` - (Dành cho Ứng viên) Xem lịch hẹn phỏng vấn AI của bạn\n" +
                  "📌 `/help` - Xem hướng dẫn này";

        await _botClient.SendTextMessageAsync(chatId, msg, parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleProfileCommandAsync(long chatId, Guid userId, UserTelegramBinding binding)
    {
        if (_botClient == null) return;

        var msg = "👤 *Thông tin liên kết tài khoản*:\n\n" +
                  $"🔹 *ID tài khoản:* `{userId}`\n" +
                  $"🔹 *Telegram Username:* `@{binding.Username ?? "N/A"}`\n" +
                  $"🔹 *Ngày liên kết:* {binding.CreatedDate.ToString("dd/MM/yyyy HH:mm")}";

        await _botClient.SendTextMessageAsync(chatId, msg, parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleCampaignsCommandAsync(long chatId, Guid userId)
    {
        if (_botClient == null) return;

        var campaigns = await _dbContext.HireAgentCampaigns
            .Where(x => x.RecruiterId == userId.ToString())
            .OrderByDescending(x => x.CreatedAt)
            .Take(10)
            .ToListAsync();

        if (campaigns.Count == 0)
        {
            await _botClient.SendTextMessageAsync(chatId, "📋 Bạn chưa có chiến dịch tuyển dụng AI nào đang chạy.");
            return;
        }

        var sb = new StringBuilder();
        sb.AppendLine("📋 *Danh sách Chiến dịch Tuyển dụng AI (Tối đa 10)*:\n");

        foreach (var c in campaigns)
        {
            var statusBadge = c.Status == "Active" ? "🟢 Active" : "🟡 " + c.Status;
            sb.AppendLine($"💼 *{c.JobName}*");
            sb.AppendLine($"   Trạng thái: {statusBadge}");
            sb.AppendLine($"   Mục tiêu: {c.TargetCount} ứng viên");
            sb.AppendLine($"   Địa điểm: {c.JobLocation ?? "Không giới hạn"}");
            sb.AppendLine();
        }

        await _botClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleInterviewsCommandAsync(long chatId, Guid userId)
    {
        if (_botClient == null) return;

        var query = from conv in _dbContext.HireAgentConversations
                    join camp in _dbContext.HireAgentCampaigns on conv.CampaignId equals camp.Id
                    where conv.CandidateId == userId.ToString()
                    orderby conv.CreatedAt descending
                    select new { conv.Status, conv.InterviewDate, conv.MatchingScore, camp.JobName };

        var list = await query.Take(10).ToListAsync();

        if (list.Count == 0)
        {
            await _botClient.SendTextMessageAsync(chatId, "📅 Bạn chưa tham gia cuộc phỏng vấn AI nào.");
            return;
        }

        var sb = new StringBuilder();
        sb.AppendLine("📅 *Danh sách Phỏng vấn AI của bạn (Tối đa 10)*:\n");

        foreach (var item in list)
        {
            var dateStr = item.InterviewDate.HasValue
                ? item.InterviewDate.Value.ToString("dd/MM/yyyy HH:mm")
                : "Chưa lên lịch";

            sb.AppendLine($"💼 *Vị trí:* {item.JobName}");
            sb.AppendLine($"   Trạng thái: {item.Status}");
            sb.AppendLine($"   Lịch hẹn: {dateStr}");
            sb.AppendLine($"   Điểm matching: {item.MatchingScore}%");
            sb.AppendLine();
        }

        await _botClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleNotificationsCommandAsync(long chatId, Guid userId)
    {
        if (_botClient == null) return;

        var notifs = await _dbContext.Notifications
            .Where(x => x.AppUserId == userId && !x.IsRead)
            .OrderByDescending(x => x.CreatedDate)
            .Take(5)
            .ToListAsync();

        if (notifs.Count == 0)
        {
            await _botClient.SendTextMessageAsync(chatId, "🔔 Bạn không có thông báo chưa đọc nào.");
            return;
        }

        var sb = new StringBuilder();
        sb.AppendLine("🔔 *Danh sách Thông báo chưa đọc mới nhất (Tối đa 5)*:\n");

        foreach (var n in notifs)
        {
            sb.AppendLine($"✉️ *{n.Title}*");
            sb.AppendLine($"   {n.Message}");
            sb.AppendLine($"   _Ngày: {n.CreatedDate.ToString("dd/MM/yyyy HH:mm")}_");
            sb.AppendLine();
        }

        await _botClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }
}

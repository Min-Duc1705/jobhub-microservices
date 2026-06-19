using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using NotificationService.Data;
using NotificationService.Hubs;
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
    private readonly IConfiguration _configuration;
    private readonly IChatService _chatService;
    private readonly IHubContext<ChatHub> _hubContext;
    private static readonly HttpClient _httpClient = new HttpClient();
    private static string? _systemBotUsername = null;

    public TelegramBotService(
        IConfiguration configuration,
        NotificationDbContext dbContext,
        ILogger<TelegramBotService> logger,
        IChatService chatService,
        IHubContext<ChatHub> hubContext)
    {
        _dbContext = dbContext;
        _logger = logger;
        _configuration = configuration;
        _chatService = chatService;
        _hubContext = hubContext;

        var token = _configuration["Telegram:BotToken"];
        if (!string.IsNullOrEmpty(token) && token != "YOUR_TELEGRAM_BOT_TOKEN")
        {
            _botClient = new TelegramBotClient(token);
        }
        else
        {
            _logger.LogWarning("Telegram Bot Token is not configured. Telegram bot services will be disabled.");
        }
    }

    private TelegramBotClient? GetBotClient(string? customToken = null)
    {
        if (!string.IsNullOrEmpty(customToken))
        {
            return new TelegramBotClient(customToken);
        }
        return _botClient;
    }

    public async Task ProcessUpdateAsync(Update update, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null || update.Message == null || string.IsNullOrEmpty(update.Message.Text))
            return;

        var message = update.Message;
        var chatId = message.Chat.Id;
        var text = message.Text.Trim();
        var username = message.Chat.Username;

        try
        {
            if (text.StartsWith("/start"))
            {
                await HandleStartCommandAsync(chatId, text, username, botToken);
            }
            else
            {
                // Check if user is bound
                UserTelegramBinding? binding = null;
                if (!string.IsNullOrEmpty(botToken))
                {
                    binding = await _dbContext.UserTelegramBindings
                        .FirstOrDefaultAsync(x => x.TelegramChatId == chatId && x.BotToken == botToken);
                }
                else
                {
                    binding = await _dbContext.UserTelegramBindings
                        .FirstOrDefaultAsync(x => x.TelegramChatId == chatId);
                }

                if (binding == null)
                {
                    await activeClient.SendTextMessageAsync(chatId,
                        "⚠️ Tài khoản của bạn chưa được liên kết với JobHub.\n\n" +
                        "Vui lòng truy cập trang *Cài đặt cá nhân* trên website JobHub và nhấn nút *Kết nối Telegram* để thực hiện liên kết.",
                        parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                    return;
                }

                if (text.StartsWith("/help"))
                {
                    await HandleHelpCommandAsync(chatId, botToken);
                }
                else if (text.StartsWith("/jobs"))
                {
                    await HandleJobsCommandAsync(chatId, binding.UserId, botToken);
                }
                else if (text.StartsWith("/campaigns"))
                {
                    await HandleCampaignsCommandAsync(chatId, binding.UserId, botToken);
                }
                else if (text.StartsWith("/interviews"))
                {
                    await HandleInterviewsCommandAsync(chatId, binding.UserId, botToken);
                }
                else if (text.StartsWith("/notifications"))
                {
                    await HandleNotificationsCommandAsync(chatId, binding.UserId, botToken);
                }
                else if (text.StartsWith("/subscribe"))
                {
                    await HandleSubscribeCommandAsync(chatId, binding.UserId, text, binding.BotToken ?? botToken);
                }
                else if (text.StartsWith("/list"))
                {
                    await HandleListCommandAsync(chatId, binding.UserId, binding.BotToken ?? botToken);
                }
                else if (text.StartsWith("/pause"))
                {
                    await HandlePauseCommandAsync(chatId, binding.UserId, text, binding.BotToken ?? botToken);
                }
                else if (text.StartsWith("/resume"))
                {
                    await HandleResumeCommandAsync(chatId, binding.UserId, text, binding.BotToken ?? botToken);
                }
                else if (text.StartsWith("/delete") || text.StartsWith("/unsubscribe"))
                {
                    await HandleDeleteCommandAsync(chatId, binding.UserId, text, binding.BotToken ?? botToken);
                }
                else if (text.StartsWith("/profile"))
                {
                    await HandleProfileCommandAsync(chatId, binding.UserId, binding, botToken);
                }
                else
                {
                    // Check if this is a reply to a previous message with a Ref GUID
                    if (message.ReplyToMessage != null && !string.IsNullOrEmpty(message.ReplyToMessage.Text))
                    {
                        var match = System.Text.RegularExpressions.Regex.Match(message.ReplyToMessage.Text, @"Ref:\s*([a-fA-F0-9-]{36})");
                        if (match.Success && Guid.TryParse(match.Groups[1].Value, out Guid partnerId))
                        {
                            var replyMsgResponse = await _chatService.SendMessageAsync(binding.UserId.ToString(), partnerId.ToString(), text, "text");
                            await _hubContext.Clients.Group(binding.UserId.ToString().ToLower()).SendAsync("ReceiveMessage", replyMsgResponse);
                            await _hubContext.Clients.Group(partnerId.ToString().ToLower()).SendAsync("ReceiveMessage", replyMsgResponse);
                            await activeClient.SendTextMessageAsync(chatId, $"✅ Đã gửi phản hồi thành công.");
                            return;
                        }
                    }

                    // ── NLP: Phát hiện ý định đặt lịch trong ngôn ngữ tự nhiên ──────────
                    // Ví dụ: "thông báo job react mỗi 1h", "cứ 30 phút gửi cho tôi ứng viên mới"
                    if (TryParseNaturalScheduleIntent(text, out string? nlpType, out string? nlpKeyword, out int nlpInterval))
                    {
                        await HandleNaturalScheduleAsync(chatId, binding.UserId, nlpType!, nlpKeyword, nlpInterval, binding.BotToken ?? botToken);
                        return;
                    }

                    // Route standard messages to AI Assistant via ChatService!
                    // Pass "telegram" as the type so ChatServiceImpl knows to reply back to Telegram
                    await _chatService.SendMessageAsync(binding.UserId.ToString(), "ai_assistant", text, "telegram");
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
        try
        {
            var binding = await _dbContext.UserTelegramBindings
                .FirstOrDefaultAsync(x => x.UserId == userId);

            if (binding != null && binding.TelegramChatId.HasValue)
            {
                var activeClient = GetBotClient(binding.BotToken);
                if (activeClient == null) return;

                var formatted = $"🔔 *{title}*\n\n{message}";
                try
                {
                    var htmlMessage = ConvertMarkdownToHtml(formatted);
                    await activeClient.SendTextMessageAsync(binding.TelegramChatId.Value, htmlMessage, parseMode: Telegram.Bot.Types.Enums.ParseMode.Html);
                }
                catch (Exception)
                {
                    await activeClient.SendTextMessageAsync(binding.TelegramChatId.Value, formatted);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi gửi thông báo đẩy qua Telegram cho User {UserId}", userId);
        }
    }

    public async Task SendTextMessageAsync(Guid userId, string message)
    {
        try
        {
            var binding = await _dbContext.UserTelegramBindings
                .FirstOrDefaultAsync(x => x.UserId == userId);

            if (binding != null && binding.TelegramChatId.HasValue)
            {
                var activeClient = GetBotClient(binding.BotToken);
                if (activeClient == null) return;

                try
                {
                    var htmlMessage = ConvertMarkdownToHtml(message);
                    await activeClient.SendTextMessageAsync(binding.TelegramChatId.Value, htmlMessage, parseMode: Telegram.Bot.Types.Enums.ParseMode.Html);
                }
                catch (Exception)
                {
                    await activeClient.SendTextMessageAsync(binding.TelegramChatId.Value, message);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi gửi tin nhắn qua Telegram cho User {UserId}", userId);
        }
    }

    private async Task HandleStartCommandAsync(long chatId, string text, string? username, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        // Check deep link binding parameter /start BIND_UserId
        var parts = text.Split(' ');
        if (parts.Length > 1 && parts[1].StartsWith("BIND_"))
        {
            var userIdStr = parts[1].Substring(5);
            if (Guid.TryParse(userIdStr, out Guid userId))
            {
                // Giải phóng TelegramChatId nếu đã được liên kết với User khác
                var otherBinding = await _dbContext.UserTelegramBindings
                    .FirstOrDefaultAsync(x => x.TelegramChatId == chatId && x.UserId != userId);
                if (otherBinding != null)
                {
                    _dbContext.UserTelegramBindings.Remove(otherBinding);
                    await _dbContext.SaveChangesAsync();
                }

                var existing = await _dbContext.UserTelegramBindings
                    .FirstOrDefaultAsync(x => x.UserId == userId);

                if (existing != null)
                {
                    existing.TelegramChatId = chatId;
                    existing.Username = username;
                    existing.CreatedDate = DateTimeOffset.UtcNow;
                    if (!string.IsNullOrEmpty(botToken))
                    {
                        existing.BotToken = botToken;
                    }
                    _dbContext.UserTelegramBindings.Update(existing);
                }
                else
                {
                    var binding = new UserTelegramBinding
                    {
                        UserId = userId,
                        TelegramChatId = chatId,
                        Username = username,
                        BotToken = botToken
                    };
                    _dbContext.UserTelegramBindings.Add(binding);
                }

                await _dbContext.SaveChangesAsync();

                await activeClient.SendTextMessageAsync(chatId,
                    "🎉 *Liên kết thành công!*\n\n" +
                    "Tài khoản của bạn đã được kết nối với JobHub. Từ bây giờ bạn sẽ nhận được thông báo đẩy trực tiếp qua Telegram này.\n\n" +
                    "Gõ `/help` để xem danh sách lệnh hỗ trợ.",
                    parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                    
                // Gửi thông báo test ngay lập tức
                await activeClient.SendTextMessageAsync(chatId,
                    "🔔 *Kiểm tra kết nối*\n\nChào mừng bạn! Hệ thống thông báo tự động JobHub đã hoạt động tốt trên thiết bị của bạn.",
                    parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                return;
            }
        }

        await activeClient.SendTextMessageAsync(chatId,
            "👋 Chào mừng bạn đến với *JobHub Bot*!\n\n" +
            "Để nhận thông báo đẩy và sử dụng các tính năng điều khiển, vui lòng vào trang *Cài đặt cá nhân* của JobHub trên trình duyệt web và click nút *Kết nối Telegram*.",
            parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleHelpCommandAsync(long chatId, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        var msg = "🤖 *Danh sách lệnh hỗ trợ trên JobHub Bot*:\n\n" +
                  "📌 `/profile` - Xem thông tin tài khoản liên kết\n" +
                  "📌 `/notifications` - Xem 5 thông báo chưa đọc\n" +
                  "📌 `/jobs` - (HR) Xem danh sách tin tuyển dụng\n" +
                  "📌 `/campaigns` - (HR) Xem chiến dịch tuyển dụng AI\n" +
                  "📌 `/interviews` - (Ứng viên) Xem lịch phỏng vấn AI\n" +
                  "📌 `/help` - Xem hướng dẫn này\n\n" +
                  "⏰ *Lệnh đặt lịch tự động:*\n" +
                  "`/subscribe <loại> [từ khoá] every <thời gian>`\n\n" +
                  "Ví dụ:\n" +
                  "  `/subscribe jobs react every 1h` → Job React mỗi 1 giờ\n" +
                  "  `/subscribe jobs every 2h` → Tất cả job mới mỗi 2 giờ\n" +
                  "  `/subscribe notifications every 30m` → Thông báo mỗi 30 phút\n" +
                  "  `/subscribe applications every 1h` → (HR) Ứng viên mới mỗi 1 giờ\n" +
                  "  `/subscribe interviews every 6h` → Cập nhật phỏng vấn mỗi 6 giờ\n" +
                  "  `/subscribe campaigns every 2h` → (HR) Tiến độ chiến dịch AI\n\n" +
                  "📋 *Quản lý lịch:*\n" +
                  "  `/list` - Xem tất cả lịch đang chạy\n" +
                  "  `/pause <id>` - Tạm dừng lịch\n" +
                  "  `/resume <id>` - Tiếp tục lịch\n" +
                  "  `/delete <id>` - Xoá lịch\n\n" +
                  "⏱ *Thời gian hỗ trợ:* `15m` `30m` `1h` `2h` `4h` `6h` `12h` `24h`\n\n" +
                  "💬 Nhắn tin bất kỳ để trò chuyện với Trợ lý AI!";

        await activeClient.SendTextMessageAsync(chatId, msg, parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleProfileCommandAsync(long chatId, Guid userId, UserTelegramBinding binding, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        var msg = "👤 *Thông tin liên kết tài khoản*:\n\n" +
                  $"🔹 *ID tài khoản:* `{userId}`\n" +
                  $"🔹 *Telegram Username:* `@{binding.Username ?? "N/A"}`\n" +
                  $"🔹 *Bot Username:* `@{binding.BotUsername ?? "Hệ thống"}`\n" +
                  $"🔹 *Ngày liên kết:* {binding.CreatedDate.ToString("dd/MM/yyyy HH:mm")}";

        await activeClient.SendTextMessageAsync(chatId, msg, parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleJobsCommandAsync(long chatId, Guid userId, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        try
        {
            var secretKey = _configuration["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
            var issuer = _configuration["Jwt:Issuer"] ?? "JobHub";
            var audience = _configuration["Jwt:Audience"] ?? "JobHubClient";
            var token = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

            var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{userId}");
            userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var userRes = await _httpClient.SendAsync(userReq);

            if (!userRes.IsSuccessStatusCode)
            {
                if ((int)userRes.StatusCode == 403)
                    await activeClient.SendTextMessageAsync(chatId, "⚠️ Bạn không có quyền thực hiện thao tác này. Tính năng `/jobs` chỉ dành cho tài khoản *Nhà tuyển dụng (HR)* hoặc *Admin*.", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                else
                    await activeClient.SendTextMessageAsync(chatId, "⚠️ Không thể xác thực tài khoản của bạn. Vui lòng thử lại sau.");
                return;
            }

            var userContent = await userRes.Content.ReadAsStringAsync();
            using var userJson = JsonDocument.Parse(userContent);
            var data = userJson.RootElement.GetProperty("data");
            
            string roleName = string.Empty;
            if (data.TryGetProperty("role", out var roleProp) && roleProp.ValueKind != JsonValueKind.Null)
            {
                roleName = roleProp.GetProperty("name").GetString() ?? "";
            }

            if (roleName != "HR" && roleName != "ADMIN")
            {
                await activeClient.SendTextMessageAsync(chatId, "⚠️ Bạn không có quyền thực hiện thao tác này. Tính năng `/jobs` chỉ dành cho tài khoản *Nhà tuyển dụng (HR)* hoặc *Admin*.", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                return;
            }

            var jobReq = new HttpRequestMessage(HttpMethod.Get, $"http://jobservice:8080/api/v1/jobs?CustomerId={userId}&pageSize=10");
            jobReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var jobRes = await _httpClient.SendAsync(jobReq);

            if (!jobRes.IsSuccessStatusCode)
            {
                await activeClient.SendTextMessageAsync(chatId, "⚠️ Đã xảy ra lỗi khi lấy danh sách công việc từ hệ thống.");
                return;
            }

            var jobContent = await jobRes.Content.ReadAsStringAsync();
            using var jobJson = JsonDocument.Parse(jobContent);
            var result = jobJson.RootElement.GetProperty("data").GetProperty("result");

            if (result.ValueKind != JsonValueKind.Array || result.GetArrayLength() == 0)
            {
                await activeClient.SendTextMessageAsync(chatId, "📋 Bạn chưa có tin tuyển dụng nào đang đăng tuyển.");
                return;
            }

            var sb = new StringBuilder();
            sb.AppendLine("📋 *Danh sách Công việc đang tuyển dụng (Tối đa 10)*:\n");

            foreach (var job in result.EnumerateArray())
            {
                var name = job.GetProperty("name").GetString();
                var status = job.GetProperty("status").GetString();
                var quantity = job.GetProperty("quantity").GetInt32();
                var location = job.TryGetProperty("location", out var locProp) && locProp.ValueKind != JsonValueKind.Null ? locProp.GetString() : "Chưa cập nhật";
                
                var salaryMin = job.TryGetProperty("salaryMin", out var minProp) && minProp.ValueKind != JsonValueKind.Null ? minProp.GetDouble() : (double?)null;
                var salaryMax = job.TryGetProperty("salaryMax", out var maxProp) && maxProp.ValueKind != JsonValueKind.Null ? maxProp.GetDouble() : (double?)null;
                var isSalaryNegotiable = job.TryGetProperty("isSalaryNegotiable", out var negoProp) && negoProp.GetBoolean();
                
                var salaryStr = isSalaryNegotiable || (!salaryMin.HasValue && !salaryMax.HasValue)
                    ? "Thỏa thuận"
                    : $"{(salaryMin.HasValue ? salaryMin.Value.ToString("N0") : "0")} - {(salaryMax.HasValue ? salaryMax.Value.ToString("N0") : "N/A")} VND";

                var statusBadge = status == "PUBLISHED" ? "🟢 Published" : "🟡 " + status;

                sb.AppendLine($"💼 *{name}*");
                sb.AppendLine($"   Trạng thái: {statusBadge}");
                sb.AppendLine($"   Số lượng: {quantity} người");
                sb.AppendLine($"   Địa điểm: {location}");
                sb.AppendLine($"   Mức lương: {salaryStr}");
                sb.AppendLine();
            }

            await activeClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi xử lý lệnh /jobs cho ChatId: {ChatId}", chatId);
            await activeClient.SendTextMessageAsync(chatId, "❌ Đã xảy ra lỗi hệ thống khi xử lý yêu cầu của bạn.");
        }
    }

    private async Task HandleCampaignsCommandAsync(long chatId, Guid userId, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        // Kiểm tra quyền: chỉ HR mới có chiến dịch tuyển dụng
        try
        {
            var secretKey = _configuration["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
            var issuer = _configuration["Jwt:Issuer"] ?? "JobHub";
            var audience = _configuration["Jwt:Audience"] ?? "JobHubClient";
            var token = InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);

            var userReq = new HttpRequestMessage(HttpMethod.Get, $"http://authservice:8080/api/v1/users/{userId}");
            userReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var userRes = await _httpClient.SendAsync(userReq);

            if (userRes.IsSuccessStatusCode)
            {
                var userContent = await userRes.Content.ReadAsStringAsync();
                using var userJson = JsonDocument.Parse(userContent);
                var data = userJson.RootElement.GetProperty("data");
                string roleName = string.Empty;
                if (data.TryGetProperty("role", out var roleProp) && roleProp.ValueKind != JsonValueKind.Null)
                    roleName = roleProp.GetProperty("name").GetString() ?? "";

                if (roleName != "HR" && roleName != "ADMIN")
                {
                    await activeClient.SendTextMessageAsync(chatId,
                        "⚠️ Bạn không có quyền thực hiện thao tác này. Tính năng `/campaigns` chỉ dành cho tài khoản *Nhà tuyển dụng (HR)* hoặc *Admin*.",
                        parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
                    return;
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi kiểm tra quyền /campaigns cho ChatId: {ChatId}", chatId);
        }

        var campaigns = await _dbContext.HireAgentCampaigns
            .Where(x => x.RecruiterId == userId.ToString())
            .OrderByDescending(x => x.CreatedAt)
            .Take(10)
            .ToListAsync();

        if (campaigns.Count == 0)
        {
            await activeClient.SendTextMessageAsync(chatId, "📋 Bạn chưa có chiến dịch tuyển dụng AI nào đang chạy.");
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

        await activeClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleInterviewsCommandAsync(long chatId, Guid userId, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        var query = from conv in _dbContext.HireAgentConversations
                    join camp in _dbContext.HireAgentCampaigns on conv.CampaignId equals camp.Id
                    where conv.CandidateId == userId.ToString()
                    orderby conv.CreatedAt descending
                    select new { conv.Status, conv.InterviewDate, conv.MatchingScore, camp.JobName };

        var list = await query.Take(10).ToListAsync();

        if (list.Count == 0)
        {
            await activeClient.SendTextMessageAsync(chatId, "📅 Bạn chưa tham gia cuộc phỏng vấn AI nào.");
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

        await activeClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private async Task HandleNotificationsCommandAsync(long chatId, Guid userId, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        var notifs = await _dbContext.Notifications
            .Where(x => x.AppUserId == userId && !x.IsRead)
            .OrderByDescending(x => x.CreatedDate)
            .Take(5)
            .ToListAsync();

        if (notifs.Count == 0)
        {
            await activeClient.SendTextMessageAsync(chatId, "🔔 Bạn không có thông báo chưa đọc nào.");
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

        await activeClient.SendTextMessageAsync(chatId, sb.ToString(), parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
    }

    private string ConvertMarkdownToHtml(string markdown)
    {
        if (string.IsNullOrEmpty(markdown)) return string.Empty;

        // 1. Escape HTML special characters
        var html = markdown
            .Replace("&", "&amp;")
            .Replace("<", "&lt;")
            .Replace(">", "&gt;");

        // 2. Process code blocks: ```code``` -> <pre>code</pre>
        var parts = html.Split(new[] { "```" }, StringSplitOptions.None);
        var sb = new StringBuilder();
        for (int i = 0; i < parts.Length; i++)
        {
            if (i % 2 == 1)
            {
                // Inside code block
                var code = parts[i];
                var firstNewline = code.IndexOf('\n');
                if (firstNewline >= 0 && firstNewline < 10)
                {
                    code = code.Substring(firstNewline + 1);
                }
                sb.Append("<pre>").Append(code.Trim()).Append("</pre>");
            }
            else
            {
                // Outside code block
                var segment = parts[i];
                
                // Process line-by-line for headers and list items
                var lines = segment.Split('\n');
                for (int l = 0; l < lines.Length; l++)
                {
                    var line = lines[l];
                    var trimmed = line.TrimStart();
                    
                    // Check headers: e.g. ### Header
                    if (trimmed.StartsWith("#"))
                    {
                        var hashCount = 0;
                        while (hashCount < trimmed.Length && trimmed[hashCount] == '#')
                        {
                            hashCount++;
                        }
                        if (hashCount < trimmed.Length && trimmed[hashCount] == ' ')
                        {
                            var headerText = trimmed.Substring(hashCount + 1).Trim();
                            line = $"<b>{headerText}</b>";
                        }
                    }
                    // Check list items: * item or - item
                    else if (trimmed.StartsWith("* ") || trimmed.StartsWith("- "))
                    {
                        var leadingSpaces = line.Substring(0, line.Length - trimmed.Length);
                        var itemText = trimmed.Substring(2).Trim();
                        line = $"{leadingSpaces}• {itemText}";
                    }

                    lines[l] = line;
                }
                segment = string.Join("\n", lines);

                // Process inline markdown: bold, italic, code, links
                segment = System.Text.RegularExpressions.Regex.Replace(segment, @"\*\*(.*?)\*\*", "<b>$1</b>");
                segment = System.Text.RegularExpressions.Regex.Replace(segment, @"\*(.*?)\*", "<i>$1</i>");
                segment = System.Text.RegularExpressions.Regex.Replace(segment, @"_(.*?)_", "<i>$1</i>");
                segment = System.Text.RegularExpressions.Regex.Replace(segment, @"`(.*?)`", "<code>$1</code>");
                segment = System.Text.RegularExpressions.Regex.Replace(segment, @"\[(.*?)\]\((.*?)\)", "<a href=\"$2\">$1</a>");

                // 3. Convert relative routing paths to clickable absolute links
                var domain = _configuration["FrontendUrl"] ?? "https://jobhub-frontend-two.vercel.app";
                domain = domain.TrimEnd('/');
                var pathPattern = @"(?<![a-zA-Z0-9:/""'.])/((?:jobs|companies|hr|candidate|admin|salary-predict|schedule|profile)(?:/[a-zA-Z0-9\-_]+)*)";
                segment = System.Text.RegularExpressions.Regex.Replace(segment, pathPattern, match =>
                {
                    var relativePath = match.Value;
                    var absoluteUrl = $"{domain}{relativePath}";
                    return $"<a href=\"{absoluteUrl}\">{relativePath}</a>";
                });

                sb.Append(segment);
            }
        }

        return sb.ToString();
    }

    public async Task<string?> GetSystemBotUsernameAsync()
    {
        if (!string.IsNullOrEmpty(_systemBotUsername))
        {
            return _systemBotUsername;
        }

        if (_botClient != null)
        {
            try
            {
                var me = await _botClient.GetMeAsync();
                _systemBotUsername = me.Username;
                return _systemBotUsername;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Lỗi khi lấy thông tin System Bot từ Telegram");
            }
        }
        return null;
    }

    public async Task InitializeWebhookAsync()
    {
        if (_botClient == null) return;

        try
        {
            var webhookDomain = _configuration["Telegram:WebhookDomain"];
            if (string.IsNullOrEmpty(webhookDomain))
            {
                _logger.LogWarning("Telegram WebhookDomain is not configured. Webhook registration skipped.");
                return;
            }

            var webhookUrl = $"{webhookDomain.TrimEnd('/')}/api/v1/telegram/webhook";
            _logger.LogInformation("Đang đăng ký Webhook cho System Bot: {WebhookUrl}", webhookUrl);
            await _botClient.SetWebhookAsync(webhookUrl);
            _logger.LogInformation("Đăng ký Webhook cho System Bot thành công!");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi đăng ký Webhook cho System Bot");
        }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // CRON SCHEDULE COMMANDS
    // ══════════════════════════════════════════════════════════════════════════

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
        // Ví dụ: /subscribe jobs react every 1h
        //        /subscribe notifications every 30m
        var parts = text.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
        // parts[0] = /subscribe
        // parts[1] = type
        // parts[n-2] = "every"
        // parts[n-1] = interval

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
        if (!_validIntervals.TryGetValue(intervalStr, out int intervalMinutes))
        {
            await activeClient.SendTextMessageAsync(chatId,
                $"❌ Chu kỳ `{intervalStr}` không hợp lệ.\n\nChu kỳ hỗ trợ: `15m` · `30m` · `1h` · `2h` · `4h` · `6h` · `12h` · `24h`",
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
        bool hasScheduleIndicator = lowerText.Contains("thông báo") ||
                                    lowerText.Contains("đặt lịch") ||
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

        // Match: (cứ|mỗi|every|sau)\s*(\d+)\s*(phút|giờ|tiếng|h|m|min)
        var matchInterval = System.Text.RegularExpressions.Regex.Match(lowerText, @"(?:cứ|mỗi|every|sau)\s*(\d+)\s*(phút|giờ|tiếng|h|m|min|s|second|minute|hour)");
        if (matchInterval.Success)
        {
            int val = int.Parse(matchInterval.Groups[1].Value);
            string unit = matchInterval.Groups[2].Value;

            if (unit.StartsWith("phút") || unit.StartsWith("m") || unit.StartsWith("min"))
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
            var matchShort = System.Text.RegularExpressions.Regex.Match(lowerText, @"\b(\d+)\s*(h|m|min|phút|giờ)\b");
            if (matchShort.Success)
            {
                int val = int.Parse(matchShort.Groups[1].Value);
                string unit = matchShort.Groups[2].Value;

                if (unit.StartsWith("phút") || unit.StartsWith("m") || unit.StartsWith("min"))
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
        return foundInterval || lowerText.Contains("thông báo") || lowerText.Contains("đăng ký") || lowerText.Contains("subscribe");
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
        if (intervalMinutes > 0)
        {
            if (intervalMinutes <= 22) finalInterval = 15;
            else if (intervalMinutes <= 45) finalInterval = 30;
            else if (intervalMinutes <= 90) finalInterval = 60;
            else if (intervalMinutes <= 180) finalInterval = 120;
            else if (intervalMinutes <= 300) finalInterval = 240;
            else if (intervalMinutes <= 540) finalInterval = 360;
            else if (intervalMinutes <= 1080) finalInterval = 720;
            else finalInterval = 1440;
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
        
        var note = "";
        if (intervalMinutes == 0)
        {
            note = "\n\n_(Tôi đã đặt chu kỳ mặc định là **1 giờ** vì chưa nhận rõ khoảng thời gian. Bạn có thể thay đổi bằng lệnh `/subscribe` hoặc xóa đi đặt lại.)_";
        }
        else if (intervalMinutes != finalInterval)
        {
            note = $"\n\n_(Lưu ý: Chu kỳ được làm tròn thành **{intervalText}** là khoảng thời gian hệ thống hỗ trợ gần nhất.)_";
        }

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

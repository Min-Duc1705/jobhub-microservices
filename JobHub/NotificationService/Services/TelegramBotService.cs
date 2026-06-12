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
                            // Send reply to partner
                            var replyMsgResponse = await _chatService.SendMessageAsync(binding.UserId.ToString(), partnerId.ToString(), text, "text");
                            
                            // Send SignalR real-time for both the sender and partner so their Web UIs update
                            await _hubContext.Clients.Group(binding.UserId.ToString().ToLower()).SendAsync("ReceiveMessage", replyMsgResponse);
                            await _hubContext.Clients.Group(partnerId.ToString().ToLower()).SendAsync("ReceiveMessage", replyMsgResponse);

                            await activeClient.SendTextMessageAsync(chatId, $"✅ Đã gửi phản hồi thành công.");
                            return;
                        }
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
                  "📌 `/profile` - Xem thông tin tài khoản liên kết hiện tại\n" +
                  "📌 `/notifications` - Xem 5 thông báo chưa đọc mới nhất\n" +
                  "📌 `/campaigns` - (Dành cho HR) Xem danh sách chiến dịch tuyển dụng AI\n" +
                  "📌 `/jobs` - (Dành cho HR) Xem danh sách công việc tuyển dụng của bạn\n" +
                  "📌 `/interviews` - (Dành cho Ứng viên) Xem lịch hẹn phỏng vấn AI của bạn\n" +
                  "📌 `/help` - Xem hướng dẫn này\n\n" +
                  "💬 Bạn cũng có thể nhắn tin trực tiếp để trò chuyện với Trợ lý AI Assistant bất cứ lúc nào!";

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
}

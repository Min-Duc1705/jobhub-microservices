using System;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using NotificationService.Models;
using Telegram.Bot;
using Telegram.Bot.Types;
using Telegram.Bot.Types.ReplyMarkups;

namespace NotificationService.Services;

public partial class TelegramBotService
{
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

        var frontendUrl = _configuration["FrontendUrl"]?.TrimEnd('/') ?? "https://jobhub-frontend-two.vercel.app";
        var loginUrl = $"{frontendUrl}/login?telegramChatId={chatId}";

        var inlineKeyboard = new InlineKeyboardMarkup(new[]
        {
            new[]
            {
                InlineKeyboardButton.WithWebApp("🔑 Đăng nhập / Liên kết ngay", new WebAppInfo { Url = loginUrl })
            },
            new[]
            {
                InlineKeyboardButton.WithUrl("🌐 Mở bằng trình duyệt", loginUrl)
            }
        });

        await activeClient.SendTextMessageAsync(chatId,
            "👋 <b>Chào mừng bạn đến với JobHub Bot!</b>\n\n" +
            "Để nhận thông báo đẩy và sử dụng các tính năng điều khiển, vui lòng đăng nhập hoặc đăng ký tài khoản JobHub để đồng bộ hóa ngay lập tức:",
            parseMode: Telegram.Bot.Types.Enums.ParseMode.Html,
            replyMarkup: inlineKeyboard);
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
                  "📌 `/send <ID_người_nhận> <nội dung>` - Gửi tin nhắn chat tới người dùng khác\n" +
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
                  "⏱ *Thời gian hỗ trợ:* Hỗ trợ tùy chọn từ `5m` trở lên (ví dụ: `5m`, `10m`, `30m`, `1h`, `2h`, v.v.)\n\n" +
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

    private async Task HandleSendChatCommandAsync(long chatId, Guid userId, string text, string? botToken = null)
    {
        var activeClient = GetBotClient(botToken);
        if (activeClient == null) return;

        var parts = text.Split(' ', 3);
        if (parts.Length < 3)
        {
            await activeClient.SendTextMessageAsync(chatId,
                "⚠️ *Cú pháp không hợp lệ.*\n\nVui lòng sử dụng cú pháp: `/send <ID_người_nhận> <nội dung>` hoặc `/chat <ID_người_nhận> <nội dung>`.",
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        var receiverIdStr = parts[1].Trim();
        var content = parts[2].Trim();

        if (!Guid.TryParse(receiverIdStr, out Guid receiverId))
        {
            await activeClient.SendTextMessageAsync(chatId, "❌ *Lỗi:* ID người nhận không đúng định dạng UUID.", parseMode: Telegram.Bot.Types.Enums.ParseMode.Markdown);
            return;
        }

        try
        {
            var replyMsgResponse = await _chatService.SendMessageAsync(userId.ToString(), receiverId.ToString(), content, "text");
            
            // Phát SignalR real-time cho cả 2 phía để cập nhật UI Web Chat
            await _hubContext.Clients.Group(userId.ToString().ToLower()).SendAsync("ReceiveMessage", replyMsgResponse);
            await _hubContext.Clients.Group(receiverId.ToString().ToLower()).SendAsync("ReceiveMessage", replyMsgResponse);

            await activeClient.SendTextMessageAsync(chatId, "✅ Đã gửi tin nhắn thành công!");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi gửi tin nhắn từ Telegram Bot: {Text}", text);
            await activeClient.SendTextMessageAsync(chatId, $"❌ Gửi tin nhắn thất bại: {ex.Message}");
        }
    }
}

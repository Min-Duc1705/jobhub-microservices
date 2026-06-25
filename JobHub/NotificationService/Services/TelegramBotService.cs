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

public partial class TelegramBotService : ITelegramBotService
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



                    // Route standard messages to AI Assistant via ChatService!
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

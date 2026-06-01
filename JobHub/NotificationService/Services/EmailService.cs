using MailKit.Net.Smtp;
using MailKit.Security;
using MimeKit;
using NotificationService.Services.Interface;

namespace NotificationService.Services;

public class EmailService : IEmailService
{
    private readonly IConfiguration _config;
    private readonly ILogger<EmailService> _logger;
    private readonly IHostEnvironment _env;

    public EmailService(IConfiguration config, ILogger<EmailService> logger, IHostEnvironment env)
    {
        _config = config;
        _logger = logger;
        _env    = env;
    }

    public async Task SendOtpEmailAsync(string toEmail, string otpCode, string otpType)
    {
        var subject = otpType == "REGISTER"
            ? "🔐 Mã xác thực tài khoản JobHub"
            : "🔑 Mã đặt lại mật khẩu JobHub";

        var body = await BuildEmailHtmlAsync(otpCode, otpType);

        var message = new MimeMessage();
        message.From.Add(new MailboxAddress(
            _config["Smtp:FromName"] ?? "JobHub Support",
            _config["Smtp:FromEmail"]));
        message.To.Add(MailboxAddress.Parse(toEmail));
        message.Subject = subject;

        var bodyBuilder = new BodyBuilder { HtmlBody = body };
        message.Body = bodyBuilder.ToMessageBody();

        using var smtp = new SmtpClient();
        await smtp.ConnectAsync(
            _config["Smtp:Host"],
            int.Parse(_config["Smtp:Port"] ?? "587"),
            SecureSocketOptions.StartTls);

        await smtp.AuthenticateAsync(
            _config["Smtp:Username"],
            _config["Smtp:Password"]);

        await smtp.SendAsync(message);
        await smtp.DisconnectAsync(true);

        _logger.LogInformation("OTP email ({Type}) sent to {Email}", otpType, toEmail);
    }

    private async Task<string> BuildEmailHtmlAsync(string otpCode, string otpType)
    {
        var templatePath = Path.Combine(_env.ContentRootPath, "Templates", "otp_email.html");

        if (!File.Exists(templatePath))
            throw new FileNotFoundException($"Email template not found at: {templatePath}");

        var (title, subtitle, action) = otpType == "REGISTER"
            ? (
                "Xác thực tài khoản của bạn",
                "Chào mừng bạn đến với <em>JobHub</em>! Vui lòng sử dụng mã xác thực dưới đây để hoàn tất quá trình thiết lập tài khoản của bạn.",
                "xác thực tài khoản"
              )
            : (
                "Đặt lại mật khẩu của bạn",
                "Chúng tôi nhận được yêu cầu <strong>đặt lại mật khẩu</strong> cho tài khoản <em>JobHub</em> của bạn. Dùng mã dưới đây để tiếp tục.",
                "đặt lại mật khẩu"
              );

        var html = await File.ReadAllTextAsync(templatePath);
        html = html.Replace("{{TITLE}}", title);
        html = html.Replace("{{SUBTITLE}}", subtitle);
        html = html.Replace("{{OTP_CODE}}", otpCode);
        html = html.Replace("{{ACTION}}", action);

        return html;
    }
}

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

    public async Task SendInterviewEmailAsync(string toEmail, string candidateName, string jobName, string dateStr, string recruiterName, string chatUrl)
    {
        var subject = "🗓️ Xác nhận lịch hẹn phỏng vấn - JobHub";
        var body = await BuildInterviewEmailHtmlAsync(candidateName, jobName, dateStr, recruiterName, chatUrl);

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

        _logger.LogInformation("Interview confirmation email sent to {Email}", toEmail);
    }

    public async Task SendInterviewEmailToRecruiterAsync(string toEmail, string candidateName, string jobName, string dateStr, string recruiterName, string dashboardUrl)
    {
        var subject = "🔔 Thông báo: Có lịch hẹn phỏng vấn mới - JobHub";
        var body = await BuildInterviewEmailRecruiterHtmlAsync(candidateName, jobName, dateStr, recruiterName, dashboardUrl);

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

        _logger.LogInformation("Interview notification email sent to Recruiter {Email}", toEmail);
    }

    private async Task<string> BuildInterviewEmailRecruiterHtmlAsync(string candidateName, string jobName, string dateStr, string recruiterName, string dashboardUrl)
    {
        var templatePath = Path.Combine(_env.ContentRootPath, "Templates", "interview_email_recruiter.html");

        if (!File.Exists(templatePath))
            throw new FileNotFoundException($"Email template not found at: {templatePath}");

        var html = await File.ReadAllTextAsync(templatePath);
        html = html.Replace("{{TITLE}}", "Thông báo Lịch phỏng vấn mới");
        html = html.Replace("{{RECRUITER_NAME}}", recruiterName);
        html = html.Replace("{{CANDIDATE_NAME}}", candidateName);
        html = html.Replace("{{JOB_NAME}}", jobName);
        html = html.Replace("{{INTERVIEW_DATE}}", dateStr);
        html = html.Replace("{{DASHBOARD_URL}}", dashboardUrl);

        return html;
    }

    private async Task<string> BuildInterviewEmailHtmlAsync(string candidateName, string jobName, string dateStr, string recruiterName, string chatUrl)
    {
        var templatePath = Path.Combine(_env.ContentRootPath, "Templates", "interview_email.html");

        if (!File.Exists(templatePath))
            throw new FileNotFoundException($"Email template not found at: {templatePath}");

        var html = await File.ReadAllTextAsync(templatePath);
        html = html.Replace("{{TITLE}}", "Xác nhận Lịch phỏng vấn thành công");
        html = html.Replace("{{CANDIDATE_NAME}}", candidateName);
        html = html.Replace("{{JOB_NAME}}", jobName);
        html = html.Replace("{{INTERVIEW_DATE}}", dateStr);
        html = html.Replace("{{RECRUITER_NAME}}", recruiterName);
        html = html.Replace("{{CHAT_URL}}", chatUrl);

        return html;
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

    public async Task SendInterviewProposalEmailAsync(string toEmail, string candidateName, string jobName, string proposedDateStr, string recruiterName, string confirmUrl)
    {
        var subject = "📅 Nhà tuyển dụng đề xuất lịch phỏng vấn - JobHub";
        var templatePath = Path.Combine(_env.ContentRootPath, "Templates", "interview_email.html");
        string body;

        if (File.Exists(templatePath))
        {
            var html = await File.ReadAllTextAsync(templatePath);
            html = html.Replace("{{TITLE}}", "Đề xuất lịch phỏng vấn từ Nhà tuyển dụng");
            html = html.Replace("{{CANDIDATE_NAME}}", candidateName);
            html = html.Replace("{{JOB_NAME}}", jobName);
            html = html.Replace("{{INTERVIEW_DATE}}", proposedDateStr);
            html = html.Replace("{{RECRUITER_NAME}}", recruiterName);
            html = html.Replace("{{CHAT_URL}}", confirmUrl);
            body = html;
        }
        else
        {
            body = $@"<h2>Xin chào {candidateName},</h2>
<p>Nhà tuyển dụng <strong>{recruiterName}</strong> đã đề xuất lịch phỏng vấn cho vị trí <strong>{jobName}</strong> vào lúc <strong>{proposedDateStr}</strong>.</p>
<p>Vui lòng truy cập <a href=""{confirmUrl}"">liên kết này</a> để xác nhận hoặc đề xuất thời gian khác.</p>
<p>Trân trọng,<br/>JobHub AI Agent</p>";
        }

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
        await smtp.AuthenticateAsync(_config["Smtp:Username"], _config["Smtp:Password"]);
        await smtp.SendAsync(message);
        await smtp.DisconnectAsync(true);

        _logger.LogInformation("Interview proposal email sent to candidate {Email}", toEmail);
    }
}

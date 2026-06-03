namespace NotificationService.Services.Interface;

public interface IEmailService
{
    Task SendOtpEmailAsync(string toEmail, string otpCode, string otpType);
    Task SendInterviewEmailAsync(string toEmail, string candidateName, string jobName, string dateStr, string recruiterName, string chatUrl);
    Task SendInterviewEmailToRecruiterAsync(string toEmail, string candidateName, string jobName, string dateStr, string recruiterName, string dashboardUrl);
}

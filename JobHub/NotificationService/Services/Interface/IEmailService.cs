namespace NotificationService.Services.Interface;

public interface IEmailService
{
    Task SendOtpEmailAsync(string toEmail, string otpCode, string otpType);
    Task SendInterviewEmailAsync(string toEmail, string candidateName, string jobName, string dateStr, string recruiterName, string chatUrl);
    Task SendInterviewEmailToRecruiterAsync(string toEmail, string candidateName, string jobName, string dateStr, string recruiterName, string dashboardUrl);
    /// <summary>Gửi email thông báo đề xuất lịch phỏng vấn từ HR tới candidate (chưa phải xác nhận chính thức)</summary>
    Task SendInterviewProposalEmailAsync(string toEmail, string candidateName, string jobName, string proposedDateStr, string recruiterName, string confirmUrl);
}

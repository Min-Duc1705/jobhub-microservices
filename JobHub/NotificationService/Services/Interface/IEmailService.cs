namespace NotificationService.Services.Interface;

public interface IEmailService
{
    Task SendOtpEmailAsync(string toEmail, string otpCode, string otpType);
}

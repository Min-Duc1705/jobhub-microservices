namespace CommonService.Events;

/// <summary>
/// Phát sinh khi cần gửi OTP qua email (đăng ký / reset password).
/// → NotificationService lắng nghe để gửi mail.
/// OtpType: "REGISTER" hoặc "RESET_PASSWORD".
/// </summary>
public class OtpRequestedEvent
{
    public string Email   { get; set; } = string.Empty;
    public string OtpCode { get; set; } = string.Empty;
    public string OtpType { get; set; } = "REGISTER";
}

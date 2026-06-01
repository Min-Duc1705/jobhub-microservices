namespace CommonService.Events;

/// <summary>
/// Phát sinh sau khi User đăng ký thành công.
/// → ProfileService lắng nghe để tạo profile tương ứng.
/// </summary>
public class UserRegisteredEvent
{
    public Guid     UserId       { get; set; }
    public string   Email        { get; set; } = string.Empty;
    public string   Username     { get; set; } = string.Empty;   // dùng làm FullName ban đầu
    public string   Role         { get; set; } = "CANDIDATE";    // CANDIDATE | HR → mạp sang CustomerType
    public DateTime RegisteredAt { get; set; }
}

namespace CommonService.Events;

/// <summary>
/// Phát sinh sau khi User đăng ký thành công.
/// → ProfileService lắng nghe để tạo profile tương ứng.
/// </summary>
public class UserRegisteredEvent
{
    public Guid     UserId       { get; set; }
    public string   Email        { get; set; } = string.Empty;
    public DateTime RegisteredAt { get; set; }
}

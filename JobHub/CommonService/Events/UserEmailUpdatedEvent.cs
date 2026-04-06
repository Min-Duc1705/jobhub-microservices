namespace CommonService.Events;

/// <summary>
/// Phát sinh khi User đổi Email.
/// → ProfileService lắng nghe để đồng bộ lại email trong profile.
/// </summary>
public class UserEmailUpdatedEvent
{
    public Guid     UserId    { get; set; }
    public string   NewEmail  { get; set; } = string.Empty;
    public DateTime UpdatedAt { get; set; }
}

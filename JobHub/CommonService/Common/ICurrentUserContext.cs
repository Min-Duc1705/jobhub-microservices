namespace CommonService.Common;

public interface ICurrentUserContext
{
    string? UserId { get; }
    string? Email { get; }
    string? Username { get; }
    string? IpAddress { get; }
    string? UserAgent { get; }
}

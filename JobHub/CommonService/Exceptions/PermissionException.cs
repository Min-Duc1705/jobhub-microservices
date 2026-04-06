namespace CommonService.Exceptions;

/// <summary>
/// Dùng để throw khi user không đủ quyền (403 Forbidden).
/// Tương đương ForbiddenException — đặt tên PermissionException cho nhất quán với MicroserviceShop.
/// </summary>
public class PermissionException : Exception
{
    public PermissionException(string message) : base(message) { }
}

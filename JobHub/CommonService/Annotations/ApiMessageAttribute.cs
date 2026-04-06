namespace CommonService.Annotations;

/// <summary>
/// Dùng để đặt message tuỳ chỉnh cho Response thành công của một endpoint.
/// Ví dụ: [ApiMessage("Lấy danh sách job thành công")]
/// </summary>
[AttributeUsage(AttributeTargets.Method)]
public class ApiMessageAttribute : Attribute
{
    public string Message { get; }

    public ApiMessageAttribute(string message)
    {
        Message = message;
    }
}

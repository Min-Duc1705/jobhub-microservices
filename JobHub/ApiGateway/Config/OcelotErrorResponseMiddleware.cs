using System.Text.Json;

namespace ApiGateway.Config;

/// <summary>
/// Middleware bọc response lỗi từ Ocelot thành JSON ApiResponse chuẩn.
///
/// Vấn đề: Ocelot xử lý JWT auth bằng pipeline riêng của nó → bypass sự kiện
/// OnChallenge/OnForbidden của JwtBearer → response 401/403 trả về body rỗng.
///
/// Giải pháp: Dùng Response.OnStarting callback thay vì swap MemoryStream.
/// Callback chỉ chạy khi response CHƯA gửi đi → chỉ can thiệp khi cần, zero overhead.
///
/// Đặt đúng chỗ: ApiGateway — vì 401/403 từ JWT xảy ra ở Gateway,
/// request không bao giờ chạm tới các microservice bên trong.
/// </summary>
public class OcelotErrorResponseMiddleware
{
    private readonly RequestDelegate _next;

    public OcelotErrorResponseMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // Đăng ký callback chạy TRƯỚC KHI response headers được gửi đi.
        // Tại thời điểm này response chưa được gửi → vẫn có thể thay đổi StatusCode,
        // ContentType và ghi body. Không cần swap stream → không tốn bộ nhớ.
        context.Response.OnStarting(async () =>
        {
            var statusCode = context.Response.StatusCode;

            // Chỉ xử lý các status lỗi phổ biến từ Ocelot/Gateway
            // 406 xảy ra khi Ocelot challenge JWT nhưng không thể trả body đúng Content-Type
            // → map về 401 Unauthorized cho nhất quán với phần còn lại của hệ thống
            if (statusCode is not (401 or 403 or 404 or 406 or 500))
                return;

            // Nếu đã có Content-Type là JSON → service đã trả body chuẩn rồi, bỏ qua
            var contentType = context.Response.ContentType ?? "";
            if (contentType.Contains("application/json"))
                return;

            var (errorName, message) = statusCode switch
            {
                401 => ("Unauthorized",          "Bạn chưa đăng nhập hoặc token đã hết hạn."),
                403 => ("Forbidden",             "Bạn không có quyền truy cập tài nguyên này."),
                404 => ("Not Found",             "Không tìm thấy tài nguyên yêu cầu trên Gateway."),
                406 => ("Unauthorized",          "Bạn chưa đăng nhập hoặc token đã hết hạn."),
                500 => ("Internal Server Error", "Lỗi hệ thống Gateway khi xử lý request."),
                _   => ("Error",                 "Đã có lỗi xảy ra.")
            };

            // Ocelot challenge JWT không có token → trả 406, normalize về 401
            var finalStatus = statusCode == 406 ? 401 : statusCode;
            context.Response.StatusCode  = finalStatus;
            context.Response.ContentType = "application/json";

            var response = new
            {
                statusCode = finalStatus,
                error      = errorName,
                message,
                data       = (object?)null
            };

            var json = JsonSerializer.Serialize(response);
            await context.Response.WriteAsync(json);
        });

        await _next(context);
    }
}

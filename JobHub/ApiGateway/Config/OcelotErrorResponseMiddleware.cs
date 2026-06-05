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
        var originalBodyStream = context.Response.Body;
        using var memoryStream = new MemoryStream();
        context.Response.Body = memoryStream;

        try
        {
            await _next(context);

            var statusCode = context.Response.StatusCode;
            var contentType = context.Response.ContentType ?? "";

            if ((statusCode is 401 or 403 or 404 or 406 or 500) && !contentType.Contains("application/json"))
            {
                var (errorName, message) = statusCode switch
                {
                    401 => ("Unauthorized",          "Bạn chưa đăng nhập hoặc token đã hết hạn."),
                    403 => ("Forbidden",             "Bạn không có quyền truy cập tài nguyên này."),
                    404 => ("Not Found",             "Không tìm thấy tài nguyên yêu cầu trên Gateway."),
                    406 => ("Unauthorized",          "Bạn chưa đăng nhập hoặc token đã hết hạn."),
                    500 => ("Internal Server Error", "Lỗi hệ thống Gateway khi xử lý request."),
                    _   => ("Error",                 "Đã có lỗi xảy ra.")
                };

                var finalStatus = statusCode == 406 ? 401 : statusCode;
                context.Response.StatusCode = finalStatus;
                context.Response.ContentType = "application/json";

                var response = new
                {
                    statusCode = finalStatus,
                    error      = errorName,
                    message,
                    data       = (object?)null
                };

                var json = JsonSerializer.Serialize(response);
                var jsonBytes = System.Text.Encoding.UTF8.GetBytes(json);

                context.Response.Headers.ContentLength = jsonBytes.Length;
                await originalBodyStream.WriteAsync(jsonBytes, 0, jsonBytes.Length);
            }
            else
            {
                memoryStream.Position = 0;
                await memoryStream.CopyToAsync(originalBodyStream);
            }
        }
        finally
        {
            context.Response.Body = originalBodyStream;
        }
    }
}

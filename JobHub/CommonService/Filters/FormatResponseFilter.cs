using CommonService.Annotations;
using CommonService.Common;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;

namespace CommonService.Filters;

/// <summary>
/// Action Filter tự động bọc mọi ObjectResult vào ApiResponse[T] chuẩn.
/// Đăng ký 1 lần trong Program.cs, tất cả Controller được áp dụng tự động.
/// </summary>
public class FormatResponseFilter : IAsyncResultFilter
{
    public async Task OnResultExecutionAsync(ResultExecutingContext context, ResultExecutionDelegate next)
    {
        // Bỏ qua Swagger UI
        var path = context.HttpContext.Request.Path.Value ?? "";
        if (path.StartsWith("/swagger") || path.StartsWith("/api-docs"))
        {
            await next();
            return;
        }

        if (context.Result is ObjectResult objectResult)
        {
            var statusCode = objectResult.StatusCode ?? context.HttpContext.Response.StatusCode;

            // Bỏ qua nếu đã là ApiResponse rồi (tránh wrap 2 lần)
            if (objectResult.Value is ApiResponse<object>)
            {
                await next();
                return;
            }

            // ---- Xử lý Response Lỗi (>= 400) ----
            if (statusCode >= 400)
            {
                context.HttpContext.Response.ContentType = "application/json";
                var errorMessage = ExtractMessage(objectResult.Value) ?? "Có lỗi xảy ra";
                objectResult.Value = new ApiResponse<object>
                {
                    StatusCode = statusCode,
                    Error      = GetErrorName(statusCode),
                    Message    = errorMessage,
                    Data       = null
                };
                await next();
                return;
            }

            // ---- Xử lý Response Thành công ----
            var apiMessageAttr = context.ActionDescriptor.EndpointMetadata
                .OfType<ApiMessageAttribute>()
                .FirstOrDefault();

            objectResult.Value = new ApiResponse<object>
            {
                StatusCode = statusCode,
                Error      = null,
                Message    = apiMessageAttr?.Message ?? "Thành công",
                Data       = objectResult.Value
            };
        }

        await next();
    }

    private static string? ExtractMessage(object? value)
    {
        if (value == null) return null;
        if (value is string str) return str;

        // FluentValidation / ModelState trả về ValidationProblemDetails có Errors dictionary
        if (value is Microsoft.AspNetCore.Mvc.ValidationProblemDetails vpd)
        {
            var messages = vpd.Errors
                .SelectMany(e => e.Value)
                .ToList();
            return messages.Any() ? string.Join(" | ", messages) : vpd.Title;
        }

        // ProblemDetails thông thường
        if (value is Microsoft.AspNetCore.Mvc.ProblemDetails pd)
            return pd.Detail ?? pd.Title;

        var prop = value.GetType().GetProperty("Message") ?? value.GetType().GetProperty("message");
        return prop?.GetValue(value)?.ToString();
    }

    private static string GetErrorName(int statusCode) => statusCode switch
    {
        400 => "Bad Request",
        401 => "Unauthorized",
        403 => "Forbidden",
        404 => "Not Found",
        409 => "Conflict",
        422 => "Unprocessable Entity",
        500 => "Internal Server Error",
        _   => "Error"
    };
}

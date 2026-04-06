using CommonService.Common;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System.Net;

namespace CommonService.Exceptions;

/// <summary>
/// Global Exception Handler — .NET 8+ approach dùng IExceptionHandler.
/// Xử lý tập trung mọi exception và trả về ApiResponse chuẩn.
/// Đăng ký: builder.Services.AddExceptionHandler&lt;GlobalExceptionHandler&gt;()
/// </summary>
public class GlobalExceptionHandler : IExceptionHandler
{
    private readonly ILogger<GlobalExceptionHandler> _logger;
    private readonly IHostEnvironment _env;

    public GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger, IHostEnvironment env)
    {
        _logger = logger;
        _env    = env;
    }

    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        _logger.LogError(exception, ">>> Exception occurred: {Message}", exception.Message);

        var response = new ApiResponse<object>();

        switch (exception)
        {
            case NotFoundException notFoundEx:
                httpContext.Response.StatusCode = (int)HttpStatusCode.NotFound;
                response.StatusCode = (int)HttpStatusCode.NotFound;
                response.Error      = "Not Found";
                response.Message    = notFoundEx.Message;
                break;

            case PermissionException permEx:
                httpContext.Response.StatusCode = (int)HttpStatusCode.Forbidden;
                response.StatusCode = (int)HttpStatusCode.Forbidden;
                response.Error      = "Forbidden";
                response.Message    = permEx.Message;
                break;

            case BadRequestException badReqEx:
                httpContext.Response.StatusCode = (int)HttpStatusCode.BadRequest;
                response.StatusCode = (int)HttpStatusCode.BadRequest;
                response.Error      = "Bad Request";
                response.Message    = badReqEx.Message;
                break;

            default:
                httpContext.Response.StatusCode = (int)HttpStatusCode.InternalServerError;
                response.StatusCode = (int)HttpStatusCode.InternalServerError;
                response.Error      = "Internal Server Error";
                // Ẩn chi tiết lỗi trong Production để bảo mật
                response.Message = _env.IsDevelopment()
                    ? exception.Message
                    : "Lỗi hệ thống nội bộ. Vui lòng thử lại sau.";
                break;
        }

        await httpContext.Response.WriteAsJsonAsync(response, cancellationToken);

        // true = exception đã được xử lý, không cần truyền cho handler nào khác
        return true;
    }
}

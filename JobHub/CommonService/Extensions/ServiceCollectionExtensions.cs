using CommonService.Common;
using CommonService.Exceptions;
using CommonService.Filters;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;

namespace CommonService.Extensions;

/// <summary>
/// Extension methods dùng chung cho mọi microservice JobHub.
/// Tập trung cấu hình Error Handling vào 1 chỗ — không lặp code ở từng Program.cs.
/// </summary>
public static class WebAppExtensions
{
    // =========================================================================
    // IServiceCollection Extensions (builder.Services.xxx)
    // =========================================================================

    /// <summary>
    /// Đăng ký GlobalExceptionHandler + ProblemDetails.
    /// Thay thế 2 dòng lặp lại ở mỗi service:
    ///   builder.Services.AddExceptionHandler&lt;GlobalExceptionHandler&gt;();
    ///   builder.Services.AddProblemDetails();
    /// </summary>
    public static IServiceCollection AddCommonApiServices(this IServiceCollection services)
    {
        services.AddExceptionHandler<GlobalExceptionHandler>();
        services.AddProblemDetails();
        return services;
    }

    // =========================================================================
    // WebApplication Extensions (app.xxx)
    // =========================================================================

    /// <summary>
    /// Đăng ký UseExceptionHandler + 404 fallback middleware.
    /// Phải đặt TRƯỚC UseAuthorization và MapControllers.
    /// Cách dùng: app.UseCommonErrorHandling("AuthService");
    /// </summary>
    public static WebApplication UseCommonErrorHandling(
        this WebApplication app,
        string serviceName = "")
    {
        // Bắt mọi exception throw (NotFoundException, BadRequestException, ...)
        // → GlobalExceptionHandler xử lý và trả ApiResponse chuẩn
        app.UseExceptionHandler();

        // Bắt 404 từ routing (route không tồn tại, không có controller action nào match)
        app.Use(async (context, next) =>
        {
            await next();

            if (context.Response.StatusCode == 404 && !context.Response.HasStarted)
            {
                context.Response.ContentType = "application/json";

                var message = string.IsNullOrWhiteSpace(serviceName)
                    ? "Không tìm thấy API endpoint yêu cầu."
                    : $"Không tìm thấy API endpoint yêu cầu trong {serviceName}.";

                var response = new ApiResponse<object>
                {
                    StatusCode = 404,
                    Error      = "Not Found",
                    Message    = message,
                    Data       = null
                };

                await context.Response.WriteAsJsonAsync(response);
            }
        });

        return app;
    }
}

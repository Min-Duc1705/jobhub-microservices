using CommonService.Common;
using CommonService.Exceptions;
using CommonService.File;
using CommonService.Filters;
using CommonService.Storage;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
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
    ///   builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
    ///   builder.Services.AddProblemDetails();
    /// </summary>
    public static IServiceCollection AddCommonApiServices(this IServiceCollection services)
    {
        services.AddExceptionHandler<GlobalExceptionHandler>();
        services.AddProblemDetails();
        services.AddScoped<ICurrentUserContext, CurrentUserContext>();
        return services;
    }

    /// <summary>
    /// Đăng ký cấu hình MinIO và service IMinioStorageService.
    /// </summary>
    public static IServiceCollection AddMinioStorage(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<MinioSettings>(configuration.GetSection(MinioSettings.SectionName));
        services.AddSingleton<IMinioStorageService, MinioStorageService>();
        return services;
    }

    /// <summary>
    /// Đăng ký <see cref="IFileService"/> (phụ thuộc vào IMinioStorageService + MinioSettings).
    /// Gọi sau <see cref="AddMinioStorage"/> trong Program.cs.
    /// </summary>
    public static IServiceCollection AddFileService(this IServiceCollection services)
    {
        services.AddScoped<IFileService, FileService>();
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

using CommonService.Caching;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace CommonService.Extensions;

public static class RedisCacheExtensions
{
    /// <summary>
    /// Đăng ký Redis DistributedCache + ICacheService singleton.
    /// instanceName dùng để prefix key Redis, tránh trùng giữa các dự án khác nhau trên cùng 1 server Redis.
    /// Ví dụ: AddCommonRedisCache(config, "JobHubAuth_")
    /// </summary>
    public static IServiceCollection AddCommonRedisCache(
        this IServiceCollection services,
        IConfiguration configuration,
        string instanceName = "JobHubAuth_")
    {
        services.AddStackExchangeRedisCache(options =>
        {
            options.Configuration = configuration.GetConnectionString("Redis");
            options.InstanceName  = instanceName;
        });

        services.AddSingleton<ICacheService, RedisCacheService>();

        return services;
    }
}

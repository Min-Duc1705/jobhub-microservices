namespace ApiGateway.Config;

public static class CorsConfiguration
{
    public const string PolicyName = "AllowSpecificOrigins";

    public static IServiceCollection AddAppCors(this IServiceCollection services)
    {
        services.AddCors(options =>
        {
            options.AddPolicy(PolicyName, builder =>
            {
                builder
                    .SetIsOriginAllowed(origin => true) // Cho phép tất cả các nguồn (gồm Ngrok, Vercel, Localhost)
                    .WithMethods("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
                    .WithHeaders("Authorization", "Content-Type", "Accept", "x-no-retry")
                    .AllowCredentials()
                    .SetPreflightMaxAge(TimeSpan.FromSeconds(3600));
            });
        });

        return services;
    }
}

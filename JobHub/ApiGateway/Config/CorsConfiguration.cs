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
                    .WithOrigins(
                        "http://localhost:5173",  // Vite dev (React)
                        "http://localhost:3000",  // React dev (CRA)
                        "http://localhost:4173"   // Vite preview
                    )
                    .WithMethods("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
                    .WithHeaders("Authorization", "Content-Type", "Accept")
                    .AllowCredentials()
                    .SetPreflightMaxAge(TimeSpan.FromSeconds(3600));
            });
        });

        return services;
    }
}

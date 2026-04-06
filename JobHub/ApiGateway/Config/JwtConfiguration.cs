using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;

namespace ApiGateway.Config;

public static class JwtConfiguration
{
    public static IServiceCollection AddAppJwt(this IServiceCollection services, IConfiguration config)
    {
        services
            .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer("Bearer", options =>
            {
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuer           = true,
                    ValidateAudience         = true,
                    ValidateLifetime         = true,
                    ValidateIssuerSigningKey = true,
                    ValidIssuer              = config["Jwt:Issuer"],
                    ValidAudience            = config["Jwt:Audience"],
                    IssuerSigningKey         = new SymmetricSecurityKey(
                        Encoding.UTF8.GetBytes(config["Jwt:SecretKey"]!)),
                    // Không cho phép trễ → token hết hạn là hết luôn
                    ClockSkew = TimeSpan.Zero,
                };

                // Lưu ý: Không dùng OnChallenge/OnForbidden ở đây vì Ocelot
                // xử lý auth bằng pipeline riêng → bypass JWT events.
                // 401/403 raw sẽ được OcelotErrorResponseMiddleware format lại.
            });

        return services;
    }
}

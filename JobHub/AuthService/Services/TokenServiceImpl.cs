using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using AuthService.Models;
using AuthService.Services.Interface;
using Microsoft.IdentityModel.Tokens;

namespace AuthService.Services;

public class TokenServiceImpl : ITokenService
{
    private readonly IConfiguration      _configuration;
    private readonly IHttpContextAccessor _httpContextAccessor;

    public TokenServiceImpl(IConfiguration configuration, IHttpContextAccessor httpContextAccessor)
    {
        _configuration       = configuration;
        _httpContextAccessor = httpContextAccessor;
    }

    // ── Access Token ──────────────────────────────────────────────────────────
    // Dùng Jwt:SecretKey — expire ngắn (30 phút)

    public string GenerateAccessToken(AppUser user)
    {
        var secretKey     = _configuration["Jwt:SecretKey"] ?? throw new Exception("Jwt:SecretKey chưa cấu hình");
        var expireSeconds = int.Parse(_configuration["Jwt:AccessTokenExpireSeconds"] ?? "1800");

        var key         = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));
        var credentials = new SigningCredentials(key, SecurityAlgorithms.HmacSha512);

        var claims = new List<Claim>
        {
            new(ClaimTypes.Email,            user.Email),
            new(ClaimTypes.NameIdentifier,   user.Id.ToString()),
            new("UserId",                    user.Id.ToString()),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
        };

        if (user.Role != null)
            claims.Add(new Claim(ClaimTypes.Role, user.Role.Name ?? ""));

        var token = new JwtSecurityToken(
            issuer:             _configuration["Jwt:Issuer"],
            audience:           _configuration["Jwt:Audience"],
            claims:             claims,
            expires:            DateTime.UtcNow.AddSeconds(expireSeconds),
            signingCredentials: credentials);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    // ── Refresh Token ─────────────────────────────────────────────────────────
    // Dùng Jwt:RefreshSecretKey riêng — expire dài (1 ngày)
    // → Tăng bảo mật: dù AccessToken key bị lộ, RefreshToken vẫn an toàn

    public string GenerateRefreshToken(AppUser user)
    {
        var secretKey     = _configuration["Jwt:RefreshSecretKey"] ?? throw new Exception("Jwt:RefreshSecretKey chưa cấu hình");
        var expireSeconds = int.Parse(_configuration["Jwt:RefreshTokenExpireSeconds"] ?? "86400");

        var key         = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));
        var credentials = new SigningCredentials(key, SecurityAlgorithms.HmacSha512);

        // RefreshToken chỉ cần đủ claim để identify user — không cần Role
        var claims = new List<Claim>
        {
            new(ClaimTypes.Email,            user.Email),
            new(ClaimTypes.NameIdentifier,   user.Id.ToString()),
            new("UserId",                    user.Id.ToString()),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
        };

        var token = new JwtSecurityToken(
            issuer:             _configuration["Jwt:Issuer"],
            audience:           _configuration["Jwt:Audience"],
            claims:             claims,
            expires:            DateTime.UtcNow.AddSeconds(expireSeconds),
            signingCredentials: credentials);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    // ── Validate Refresh Token ─────────────────────────────────────────────────
    // Dùng Jwt:RefreshSecretKey — phải khớp với key dùng khi tạo

    public ClaimsPrincipal? ValidateRefreshToken(string token)
    {
        try
        {
            var secretKey = _configuration["Jwt:RefreshSecretKey"] ?? throw new Exception("Jwt:RefreshSecretKey chưa cấu hình");
            var key       = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));

            var validationParams = new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey         = key,
                ValidateIssuer           = true,
                ValidIssuer              = _configuration["Jwt:Issuer"],
                ValidateAudience         = true,
                ValidAudience            = _configuration["Jwt:Audience"],
                ValidateLifetime         = true,
                ClockSkew                = TimeSpan.Zero  // Không cho phép trễ hơn 0 giây
            };

            return new JwtSecurityTokenHandler().ValidateToken(token, validationParams, out _);
        }
        catch
        {
            return null; // Token không hợp lệ hoặc đã hết hạn
        }
    }

    // ── Current User ──────────────────────────────────────────────────────────

    public string? GetCurrentUserEmail()
        => _httpContextAccessor.HttpContext?.User?.FindFirst(ClaimTypes.Email)?.Value;
}

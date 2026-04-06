using System.Security.Claims;
using AuthService.Models;

namespace AuthService.Services.Interface
{
    public interface ITokenService
    {
        string GenerateAccessToken(AppUser user);
        string GenerateRefreshToken(AppUser user);
        ClaimsPrincipal? ValidateRefreshToken(string token);
        string? GetCurrentUserEmail();
    }
}

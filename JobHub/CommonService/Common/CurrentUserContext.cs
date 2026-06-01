using System.Security.Claims;
using Microsoft.AspNetCore.Http;

namespace CommonService.Common;

public class CurrentUserContext : ICurrentUserContext
{
    private readonly IHttpContextAccessor _httpContextAccessor;

    public CurrentUserContext(IHttpContextAccessor httpContextAccessor)
    {
        _httpContextAccessor = httpContextAccessor;
    }

    private HttpContext? HttpContext => _httpContextAccessor.HttpContext;

    public string? UserId => HttpContext?.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                             ?? HttpContext?.User?.FindFirst("sub")?.Value;

    public string? Email => HttpContext?.User?.FindFirst(ClaimTypes.Email)?.Value 
                            ?? HttpContext?.User?.FindFirst("email")?.Value;

    public string? Username => HttpContext?.User?.FindFirst(ClaimTypes.Name)?.Value 
                               ?? HttpContext?.User?.FindFirst("Username")?.Value 
                               ?? HttpContext?.User?.FindFirst("username")?.Value;

    public string? IpAddress => HttpContext?.Connection?.RemoteIpAddress?.ToString();

    public string? UserAgent => HttpContext?.Request?.Headers["User-Agent"].ToString();
}

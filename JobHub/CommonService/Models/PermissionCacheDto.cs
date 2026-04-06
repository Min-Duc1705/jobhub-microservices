namespace CommonService.Models;

/// <summary>
/// DTO lưu thông tin 1 Permission vào Redis Cache.
/// Key Redis: "perm:{email}" — Value: mảng PermissionCacheDto[]
/// TTL bằng với thời gian sống của AccessToken.
/// </summary>
public class PermissionCacheDto
{
    public string ApiPath { get; set; } = string.Empty;
    public string Method  { get; set; } = string.Empty;
    public string Module  { get; set; } = string.Empty;
}

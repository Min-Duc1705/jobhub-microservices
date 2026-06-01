using CommonService.Models;
using CompanyService.Models.Enums;

namespace CompanyService.Models;

/// <summary>
/// Đại diện cho thông tin một Doanh nghiệp (CompanyService bounded context).
/// </summary>
public class Company : EntityAuditableBase<Guid>
{
    public string  Name         { get; set; } = string.Empty;
    public string? Description  { get; set; }
    public string? Address      { get; set; }
    public string? Logo         { get; set; }          // URL logo
    public string? CoverImage   { get; set; }          // URL ảnh bìa hero
    public string? Industry     { get; set; }          // Ngành nghề
    public CompanySize? CompanySize { get; set; }
    public string? Website      { get; set; }
    public string? ContactEmail { get; set; }
    public string? TaxCode      { get; set; }          // Mã số thuế
    public bool    IsVerified   { get; set; } = false; // Admin xác minh

    /// <summary>Danh sách URL ảnh văn phòng / hoạt động (tối đa 4), lưu JSON.</summary>
    public List<string> ActivityImages { get; set; } = new();
}

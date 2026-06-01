using CompanyService.Models.Enums;

namespace CompanyService.Models.Response;

public class CompanyResponse
{
    public Guid         Id           { get; set; }
    public string       Name         { get; set; } = string.Empty;
    public string?      Description  { get; set; }
    public string?      Address      { get; set; }
    public string?      Logo         { get; set; }
    public string?      CoverImage   { get; set; }
    public string?      Industry     { get; set; }
    public CompanySize? CompanySize  { get; set; }
    public string?      Website      { get; set; }
    public string?      ContactEmail { get; set; }
    public string?      TaxCode      { get; set; }
    public bool         IsVerified   { get; set; }
    public List<string> ActivityImages { get; set; } = new();  // Ảnh văn phòng/hoạt động
    public DateTimeOffset CreatedDate { get; set; }
    public DateTimeOffset? LastModifiedDate { get; set; }
}

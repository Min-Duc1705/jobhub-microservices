using CompanyService.Models.Enums;

namespace CompanyService.Models.Request;

/// <summary>Tạo mới doanh nghiệp</summary>
public class CreateCompanyRequest
{
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
    public List<string>? ActivityImages { get; set; }  // Ảnh văn phòng/hoạt động (tối đa 4)
}

/// <summary>Cập nhật thông tin doanh nghiệp</summary>
public class UpdateCompanyRequest
{
    public string?      Name         { get; set; }
    public string?      Description  { get; set; }
    public string?      Address      { get; set; }
    public string?      Logo         { get; set; }
    public string?      CoverImage   { get; set; }
    public string?      Industry     { get; set; }
    public CompanySize? CompanySize  { get; set; }
    public string?      Website      { get; set; }
    public string?      ContactEmail { get; set; }
    public string?      TaxCode      { get; set; }
    public List<string>? ActivityImages { get; set; }  // Ảnh văn phòng/hoạt động (tối đa 4)
}

/// <summary>Bộ lọc danh sách doanh nghiệp có phân trang</summary>
public class CompanyFilterRequest
{
    public string? SearchTerm   { get; set; }           // Tìm theo tên, ngành
    public string? Industry     { get; set; }           // Lọc theo ngành
    public CompanySize? CompanySize { get; set; }       // Lọc theo quy mô
    public bool?   IsVerified   { get; set; }           // Lọc trạng thái xác minh
    public string  SortBy       { get; set; } = "createdDate";
    public bool    IsDescending { get; set; } = true;
    public int     PageNumber   { get; set; } = 1;
    public int     PageSize     { get; set; } = 10;
}

public class ImportCompanyDto
{
    [System.ComponentModel.DataAnnotations.Required(ErrorMessage = "Tên công ty không được để trống")]
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? Address { get; set; }
    public string? Industry { get; set; }
    public string? CompanySize { get; set; } // "STARTUP", "SME", "ENTERPRISE"
    public string? Website { get; set; }
    public string? ContactEmail { get; set; }
    public string? TaxCode { get; set; }
}

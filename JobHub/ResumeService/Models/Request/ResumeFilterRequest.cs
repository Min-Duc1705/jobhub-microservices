namespace ResumeService.Models.Request;

/// <summary>Bộ lọc tìm kiếm Resume với phân trang.</summary>
public class ResumeFilterRequest
{
    public string?  SearchTerm  { get; set; }       // Tìm theo tiêu đề CV
    public Guid?    CustomerId  { get; set; }        // Lọc theo ứng viên
    public bool?    IsDefault   { get; set; }        // Lọc CV mặc định
    public string   SortBy      { get; set; } = "createdDate";
    public bool     IsDescending { get; set; } = true;
    public int      PageNumber  { get; set; } = 1;
    public int      PageSize    { get; set; } = 10;
}

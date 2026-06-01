using ResumeService.Models.Enums;

namespace ResumeService.Models.Request;

/// <summary>Bộ lọc tìm kiếm Application với phân trang.</summary>
public class ApplicationFilterRequest
{
    public Guid?              CustomerId  { get; set; }  // Lọc theo ứng viên
    public Guid?              JobId       { get; set; }  // Lọc theo tin tuyển dụng
    public ApplicationStatus? Status      { get; set; }  // Lọc theo trạng thái
    public string   SortBy      { get; set; } = "createdDate";
    public bool     IsDescending { get; set; } = true;
    public int      PageNumber  { get; set; } = 1;
    public int      PageSize    { get; set; } = 10;
}

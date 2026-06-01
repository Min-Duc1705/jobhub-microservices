using ResumeService.Models.Enums;

namespace ResumeService.Models.Request;

/// <summary>NTD cập nhật trạng thái đơn ứng tuyển (duyệt / từ chối).</summary>
public class UpdateApplicationStatusRequest
{
    public ApplicationStatus Status { get; set; }
    public string? ReviewNote       { get; set; }
}

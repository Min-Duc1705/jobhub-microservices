namespace ResumeService.Models.Request;

/// <summary>Ứng viên nộp đơn ứng tuyển.</summary>
public class CreateApplicationRequest
{
    /// <summary>ID tin tuyển dụng (từ JobService).</summary>
    public Guid JobId { get; set; }

    /// <summary>ID của CV dùng để ứng tuyển.</summary>
    public Guid ResumeId { get; set; }

    /// <summary>Thư xin việc đi kèm (tùy chọn).</summary>
    public string? CoverLetter { get; set; }
}

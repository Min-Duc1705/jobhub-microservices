using CommonService.Models;
using ResumeService.Models.Enums;

namespace ResumeService.Models;

/// <summary>
/// Phiên ứng tuyển — lưu trữ mỗi lần ứng viên nộp CV cho một tin tuyển dụng.
/// Tách riêng khỏi Resume để một ứng viên có thể dùng cùng 1 CV ứng tuyển nhiều Job.
/// JobId là cross-service reference (không FK sang JobService DB).
/// </summary>
public class Application : EntityAuditableBase<Guid>
{
    /// <summary>Ứng viên ứng tuyển (cross-service reference).</summary>
    public Guid CustomerId { get; set; }

    /// <summary>Tin tuyển dụng ứng tuyển (cross-service reference sang JobService).</summary>
    public Guid JobId { get; set; }

    /// <summary>CV đã nộp cho lần ứng tuyển này (FK nội bộ ResumeService).</summary>
    public Guid ResumeId { get; set; }

    /// <summary>Thư xin việc đi kèm.</summary>
    public string? CoverLetter { get; set; }

    /// <summary>Trạng thái xử lý đơn ứng tuyển.</summary>
    public ApplicationStatus Status { get; set; } = ApplicationStatus.PENDING;

    /// <summary>Ghi chú nội bộ của NTD khi review.</summary>
    public string? ReviewNote { get; set; }

    // ── Navigation (chỉ FK nội bộ service) ────────────────────────────────────
    public Resume Resume { get; set; } = null!;
}

using System;
using CommonService.Models;

namespace ResumeService.Models;

/// <summary>
/// Bảng lịch phỏng vấn dùng chung cho cả luồng AI (Hire Agent) và Đặt lịch thủ công.
/// </summary>
public class Interview : EntityAuditableBase<Guid>
{
    /// <summary>Vị trí tin tuyển dụng.</summary>
    public Guid JobId { get; set; }

    /// <summary>ID Ứng viên (Customer).</summary>
    public Guid CandidateId { get; set; }

    /// <summary>ID Nhà tuyển dụng (Recruiter).</summary>
    public Guid RecruiterId { get; set; }

    /// <summary>Ngày giờ phỏng vấn chính thức.</summary>
    public DateTimeOffset InterviewDate { get; set; }

    /// <summary>Loại phỏng vấn: Technical, Cultural, Final.</summary>
    public string Type { get; set; } = "Technical";

    /// <summary>Trạng thái lịch hẹn: PendingConfirm, Scheduled, Rescheduled, Cancelled, Completed.</summary>
    public string Status { get; set; } = "PendingConfirm";

    /// <summary>Link cuộc họp online (Google Meet / Zoom).</summary>
    public string? MeetingLink { get; set; }

    /// <summary>Địa chỉ phỏng vấn nếu offline.</summary>
    public string? Location { get; set; }

    /// <summary>Ghi chú của NTD dành cho ứng viên.</summary>
    public string? Notes { get; set; }
}

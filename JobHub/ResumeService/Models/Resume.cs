using CommonService.Models;

namespace ResumeService.Models;

/// <summary>
/// Tài liệu CV — ứng viên upload lên hệ thống.
/// Một ứng viên có thể có nhiều bản CV khác nhau.
/// CustomerId là cross-service reference (không FK cross-service).
/// </summary>
public class Resume : EntityAuditableBase<Guid>
{
    /// <summary>Ứng viên sở hữu CV (Customer.Type == CANDIDATE).</summary>
    public Guid CustomerId { get; set; }

    /// <summary>Tiêu đề CV (VD: "CV Backend Developer 2026").</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Link lưu file CV trên Object Storage (S3/MinIO). Null nếu là Online CV.</summary>
    public string? Url { get; set; }

    /// <summary>Extracted plain text from PDF/DOCX, used by AI scoring.</summary>
    public string? ExtractedText { get; set; }

    /// <summary>CV mặc định khi ứng tuyển nhanh.</summary>
    public bool IsDefault { get; set; } = false;

    // ── Online CV Builder fields ──────────────────────────────────────────────

    /// <summary>True nếu CV được tạo bằng Online Builder (không phải file upload).</summary>
    public bool IsOnlineCv { get; set; } = false;

    /// <summary>ID mẫu template: 1=Modern, 2=Classic, ...</summary>
    public int? TemplateId { get; set; }

    /// <summary>Nội dung CV dạng JSON (serialize của ResumeContent).</summary>
    public string? ContentJson { get; set; }

    // ── Navigation ───────────────────────────────────────────────────────────
    public ICollection<Application> Applications { get; set; } = new List<Application>();
}

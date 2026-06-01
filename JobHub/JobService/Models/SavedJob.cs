namespace JobService.Models;

/// <summary>Ứng viên bookmark tin tuyển dụng để xem lại sau.</summary>
public class SavedJob
{
    public Guid JobId      { get; set; }
    public Guid CustomerId { get; set; }  // ID của Candidate (cross-service reference)

    public DateTimeOffset SavedAt { get; set; } = DateTimeOffset.UtcNow;
    public string? Note           { get; set; }

    // ── Navigation ───────────────────────────────────────────────────────────
    public Job Job { get; set; } = null!;
}

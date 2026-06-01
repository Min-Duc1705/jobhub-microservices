namespace JobService.Models;

/// <summary>Bảng N-N nối Job ↔ Skill (yêu cầu kỹ năng của tin tuyển dụng).</summary>
public class JobSkill
{
    public Guid JobId   { get; set; }
    public Guid SkillId { get; set; }

    // ── Navigation ───────────────────────────────────────────────────────────
    public Job   Job   { get; set; } = null!;
    public Skill Skill { get; set; } = null!;
}

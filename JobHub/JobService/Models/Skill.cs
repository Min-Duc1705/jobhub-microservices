using CommonService.Models;

namespace JobService.Models;

/// <summary>
/// Từ điển kỹ năng — JobService là master source.
/// ProfileService chứa replica read-only đồng bộ qua event SkillCreated/SkillUpdated/SkillDeleted.
/// </summary>
public class Skill : EntityAuditableBase<Guid>
{
    public string Name { get; set; } = string.Empty;

    // ── Navigation ───────────────────────────────────────────────────────────
    public ICollection<JobSkill> JobSkills { get; set; } = new List<JobSkill>();
}

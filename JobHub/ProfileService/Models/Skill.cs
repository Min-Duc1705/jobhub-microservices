using CommonService.Models;

namespace ProfileService.Models;

/// <summary>
/// Hệ thống Profile chỉ lưu bản thu gọn (replica) của bảng Skill.
/// Bản master sẽ nằm ở JobService.
/// </summary>
public class Skill : EntityAuditableBase<Guid>
{
    public string Name { get; set; } = string.Empty;

    public virtual ICollection<CustomerSkill> CustomerSkills { get; set; } = new List<CustomerSkill>();
}

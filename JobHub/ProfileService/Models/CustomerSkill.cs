namespace ProfileService.Models;

public class CustomerSkill
{
    public Guid CustomerId { get; set; }
    public virtual Customer Customer { get; set; } = null!;

    public Guid SkillId { get; set; }
    public virtual Skill Skill { get; set; } = null!;

    public int? YearsOfExperience { get; set; }
}

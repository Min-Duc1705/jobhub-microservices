namespace CommonService.Events;

public class SkillUpdatedEvent
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
}

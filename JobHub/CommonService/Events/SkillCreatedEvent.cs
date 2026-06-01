namespace CommonService.Events;

public class SkillCreatedEvent
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
}

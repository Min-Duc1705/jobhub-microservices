namespace CommonService.Events;

public class CompanyUpdatedEvent
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Logo { get; set; }
}

using System;

namespace CommonService.Events;

public class ApplicationStatusChangedEvent
{
    public Guid ApplicationId { get; set; }
    public Guid CustomerId { get; set; }
    public Guid JobId { get; set; }
    public string Status { get; set; } = string.Empty;
    public string? ReviewNote { get; set; }
}

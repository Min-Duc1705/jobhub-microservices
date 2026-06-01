using System;

namespace CommonService.Events;

public class ApplicationSubmittedEvent
{
    public Guid ApplicationId { get; set; }
    public Guid CustomerId { get; set; }
    public Guid JobId { get; set; }
    public DateTime SubmittedAt { get; set; }
}

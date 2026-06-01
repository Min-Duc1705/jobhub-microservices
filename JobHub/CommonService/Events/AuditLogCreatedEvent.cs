using System;

namespace CommonService.Events;

public class AuditLogCreatedEvent
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string? UserId { get; set; }
    public string? Email { get; set; }
    public string? Username { get; set; }
    public string Action { get; set; } = string.Empty; // CREATE, UPDATE, DELETE
    public string EntityName { get; set; } = string.Empty;
    public string EntityId { get; set; } = string.Empty;
    public string? ChangesJson { get; set; } // {"FieldName": {"old": "A", "new": "B"}}
    public string? IpAddress { get; set; }
    public string? UserAgent { get; set; }
    public DateTimeOffset Timestamp { get; set; } = DateTimeOffset.UtcNow;
}

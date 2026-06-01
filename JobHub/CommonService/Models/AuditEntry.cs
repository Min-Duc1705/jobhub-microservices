using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.ChangeTracking;
using CommonService.Events;

namespace CommonService.Models;

public class AuditEntry
{
    public AuditEntry(EntityEntry entry)
    {
        Entry = entry;
    }

    public EntityEntry Entry { get; }
    public string? UserId { get; set; }
    public string? Email { get; set; }
    public string? Username { get; set; }
    public string Action { get; set; } = string.Empty;
    public string EntityName { get; set; } = string.Empty;
    public string EntityId { get; set; } = string.Empty;
    public Dictionary<string, object?> OriginalValues { get; } = new();
    public Dictionary<string, object?> NewValues { get; } = new();
    public List<PropertyEntry> TemporaryProperties { get; } = new();

    public bool HasTemporaryProperties => TemporaryProperties.Any();

    public AuditLogCreatedEvent ToEvent(string? ip, string? ua)
    {
        var changes = new Dictionary<string, object>();
        foreach (var propName in NewValues.Keys)
        {
            OriginalValues.TryGetValue(propName, out var oldVal);
            NewValues.TryGetValue(propName, out var newVal);
            changes[propName] = new { old = oldVal, @new = newVal };
        }

        return new AuditLogCreatedEvent
        {
            UserId = UserId,
            Email = Email,
            Username = Username,
            Action = Action,
            EntityName = EntityName,
            EntityId = EntityId,
            ChangesJson = changes.Count > 0 ? JsonSerializer.Serialize(changes) : null,
            IpAddress = ip,
            UserAgent = ua,
            Timestamp = DateTimeOffset.UtcNow
        };
    }
}

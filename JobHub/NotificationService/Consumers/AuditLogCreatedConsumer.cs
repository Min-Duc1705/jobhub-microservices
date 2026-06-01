using System.Threading.Tasks;
using CommonService.Events;
using MassTransit;
using Microsoft.Extensions.Logging;
using NotificationService.Data;
using NotificationService.Models;

namespace NotificationService.Consumers;

public class AuditLogCreatedConsumer : IConsumer<AuditLogCreatedEvent>
{
    private readonly NotificationDbContext _dbContext;
    private readonly ILogger<AuditLogCreatedConsumer> _logger;

    public AuditLogCreatedConsumer(NotificationDbContext dbContext, ILogger<AuditLogCreatedConsumer> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task Consume(ConsumeContext<AuditLogCreatedEvent> context)
    {
        var msg = context.Message;
        _logger.LogInformation("Received AuditLogCreatedEvent: Action={Action}, Entity={EntityName}, Id={EntityId}, User={Email}",
            msg.Action, msg.EntityName, msg.EntityId, msg.Email);

        var auditLog = new AuditLog
        {
            Id = msg.Id,
            UserId = msg.UserId,
            Email = msg.Email,
            Username = msg.Username,
            Action = msg.Action,
            EntityName = msg.EntityName,
            EntityId = msg.EntityId,
            ChangesJson = msg.ChangesJson,
            IpAddress = msg.IpAddress,
            UserAgent = msg.UserAgent,
            Timestamp = msg.Timestamp
        };

        _dbContext.AuditLogs.Add(auditLog);
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Saved Audit Log record {Id} successfully.", auditLog.Id);
    }
}

using CommonService.Models.Interface;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using NotificationService.Models;
using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace NotificationService.Data;

public class NotificationDbContext : DbContext
{
    public NotificationDbContext(DbContextOptions<NotificationDbContext> options) : base(options)
    {
    }

    public DbSet<Notification> Notifications { get; set; } = null!;
    public DbSet<AuditLog> AuditLogs { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Notification>(entity =>
        {
            entity.HasKey(n => n.Id);
            entity.HasIndex(n => n.AppUserId).HasDatabaseName("IX_Notifications_AppUserId");
            entity.HasIndex(n => n.IsDeleted).HasDatabaseName("IX_Notifications_IsDeleted");
            entity.HasQueryFilter(n => !n.IsDeleted);
        });

        modelBuilder.Entity<AuditLog>(entity =>
        {
            entity.HasKey(a => a.Id);
            entity.HasIndex(a => a.Email).HasDatabaseName("IX_AuditLogs_Email");
            entity.HasIndex(a => a.Username).HasDatabaseName("IX_AuditLogs_Username");
            entity.HasIndex(a => a.Action).HasDatabaseName("IX_AuditLogs_Action");
            entity.HasIndex(a => a.EntityName).HasDatabaseName("IX_AuditLogs_EntityName");
            entity.HasIndex(a => a.Timestamp).HasDatabaseName("IX_AuditLogs_Timestamp");
            entity.HasIndex(a => a.IsDeleted).HasDatabaseName("IX_AuditLogs_IsDeleted");
            entity.HasQueryFilter(a => !a.IsDeleted);
        });
    }

    public override Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        var entries = ChangeTracker.Entries()
            .Where(e => e.State == EntityState.Added || e.State == EntityState.Modified);

        foreach (var entry in entries)
        {
            if (entry.Entity is IDateTracking dateTracking)
            {
                if (entry.State == EntityState.Added)
                    dateTracking.CreatedDate = DateTimeOffset.UtcNow;
                else
                    dateTracking.LastModifiedDate = DateTimeOffset.UtcNow;
            }

            if (entry.Entity is IUserTracking userTracking)
            {
                if (entry.State == EntityState.Added)
                    userTracking.CreatedBy = "system";
                else
                    userTracking.LastModifiedBy = "system";
            }
        }

        return base.SaveChangesAsync(cancellationToken);
    }
}

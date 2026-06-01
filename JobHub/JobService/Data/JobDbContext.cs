using CommonService.Models.Interface;
using JobService.Models;
using Microsoft.EntityFrameworkCore;
using CommonService.Common;
using CommonService.Models;
using MassTransit;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace JobService.Data;

public class JobDbContext : DbContext
{
    private readonly ICurrentUserContext _currentUserContext;
    private readonly IPublishEndpoint _publishEndpoint;

    public JobDbContext(
        DbContextOptions<JobDbContext> options,
        ICurrentUserContext currentUserContext,
        IPublishEndpoint publishEndpoint) : base(options)
    {
        _currentUserContext = currentUserContext;
        _publishEndpoint = publishEndpoint;
    }

    // ── DbSets ────────────────────────────────────────────────────────────────
    public DbSet<Job>      Jobs      { get; set; } = null!;
    public DbSet<Skill>    Skills    { get; set; } = null!;
    public DbSet<JobSkill> JobSkills { get; set; } = null!;
    public DbSet<SavedJob> SavedJobs { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ── Job ───────────────────────────────────────────────────────────────
        modelBuilder.Entity<Job>(entity =>
        {
            entity.HasKey(j => j.Id);

            entity.Property(j => j.Level).HasConversion<string>();
            entity.Property(j => j.JobType).HasConversion<string>();
            entity.Property(j => j.Status).HasConversion<string>();
            entity.Property(j => j.Name).IsRequired().HasMaxLength(300);
            entity.Property(j => j.SalaryCurrency).HasMaxLength(10);

            // Indexes phục vụ tìm kiếm và filter
            entity.HasIndex(j => j.CompanyId).HasDatabaseName("IX_Jobs_CompanyId");
            entity.HasIndex(j => j.CustomerId).HasDatabaseName("IX_Jobs_CustomerId");
            entity.HasIndex(j => j.Status).HasDatabaseName("IX_Jobs_Status");
            entity.HasIndex(j => j.Level).HasDatabaseName("IX_Jobs_Level");
            entity.HasIndex(j => j.JobType).HasDatabaseName("IX_Jobs_JobType");
            entity.HasIndex(j => j.IsDeleted).HasDatabaseName("IX_Jobs_IsDeleted");
            entity.HasIndex(j => j.EndDate).HasDatabaseName("IX_Jobs_EndDate");
            entity.Property(j => j.Category).HasMaxLength(100);
            entity.HasIndex(j => j.Category).HasDatabaseName("IX_Jobs_Category");

            // Soft-delete query filter
            entity.HasQueryFilter(j => !j.IsDeleted);
        });

        // ── Skill ─────────────────────────────────────────────────────────────
        modelBuilder.Entity<Skill>(entity =>
        {
            entity.HasKey(s => s.Id);
            entity.Property(s => s.Name).IsRequired().HasMaxLength(100);
            entity.HasIndex(s => s.Name).IsUnique().HasDatabaseName("IX_Skills_Name");
            entity.HasIndex(s => s.IsDeleted).HasDatabaseName("IX_Skills_IsDeleted");

            entity.HasQueryFilter(s => !s.IsDeleted);
        });

        // ── JobSkill (junction N-N) ────────────────────────────────────────────
        modelBuilder.Entity<JobSkill>(entity =>
        {
            entity.HasKey(js => new { js.JobId, js.SkillId });

            entity.HasOne(js => js.Job)
                  .WithMany(j => j.JobSkills)
                  .HasForeignKey(js => js.JobId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(js => js.Skill)
                  .WithMany(s => s.JobSkills)
                  .HasForeignKey(js => js.SkillId)
                  .OnDelete(DeleteBehavior.Restrict); // Không xóa Skill nếu đang có Job dùng

            // Query filter khớp với filter của Job và Skill
            entity.HasQueryFilter(js => !js.Job.IsDeleted && !js.Skill.IsDeleted);
        });

        // ── SavedJob ──────────────────────────────────────────────────────────
        modelBuilder.Entity<SavedJob>(entity =>
        {
            entity.HasKey(sv => new { sv.JobId, sv.CustomerId });

            entity.HasOne(sv => sv.Job)
                  .WithMany(j => j.SavedJobs)
                  .HasForeignKey(sv => sv.JobId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(sv => sv.CustomerId).HasDatabaseName("IX_SavedJobs_CustomerId");
            entity.HasIndex(sv => sv.SavedAt).HasDatabaseName("IX_SavedJobs_SavedAt");

            // Query filter: Bỏ qua các SavedJob của tin tuyển dụng đã bị xoá
            entity.HasQueryFilter(sv => !sv.Job.IsDeleted);
        });
    }

    // ── Tự động gán Audit Fields và gửi Audit Log khi SaveChanges ─────────────
    public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        ApplyAuditFields();

        var auditEntries = CaptureAuditEntries();

        var result = await base.SaveChangesAsync(cancellationToken);

        if (auditEntries.Any())
        {
            await PublishAuditEventsAsync(auditEntries);
        }

        return result;
    }

    private void ApplyAuditFields()
    {
        var currentUser = _currentUserContext.Email ?? "system";
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
                    userTracking.CreatedBy = currentUser;
                else
                    userTracking.LastModifiedBy = currentUser;
            }
        }
    }

    private List<AuditEntry> CaptureAuditEntries()
    {
        var auditEntries = new List<AuditEntry>();
        var targetEntries = ChangeTracker.Entries()
            .Where(e => e.State == EntityState.Added || e.State == EntityState.Modified || e.State == EntityState.Deleted);

        foreach (var entry in targetEntries)
        {
            var auditEntry = new AuditEntry(entry)
            {
                UserId = _currentUserContext.UserId,
                Email = _currentUserContext.Email,
                Username = _currentUserContext.Username,
                EntityName = entry.Entity.GetType().Name
            };
            auditEntries.Add(auditEntry);

            switch (entry.State)
            {
                case EntityState.Added:
                    auditEntry.Action = "CREATE";
                    foreach (var prop in entry.Properties)
                    {
                        if (prop.IsTemporary)
                        {
                            auditEntry.TemporaryProperties.Add(prop);
                            continue;
                        }
                        auditEntry.NewValues[prop.Metadata.Name] = prop.CurrentValue;
                    }
                    break;

                case EntityState.Deleted:
                    auditEntry.Action = "DELETE";
                    foreach (var prop in entry.Properties)
                    {
                        auditEntry.OriginalValues[prop.Metadata.Name] = prop.OriginalValue;
                    }
                    break;

                case EntityState.Modified:
                    auditEntry.Action = "UPDATE";
                    foreach (var prop in entry.Properties)
                    {
                        if (prop.IsModified && !Equals(prop.OriginalValue, prop.CurrentValue))
                        {
                            auditEntry.OriginalValues[prop.Metadata.Name] = prop.OriginalValue;
                            auditEntry.NewValues[prop.Metadata.Name] = prop.CurrentValue;
                        }
                    }
                    break;
            }
        }

        return auditEntries;
    }

    private async Task PublishAuditEventsAsync(List<AuditEntry> auditEntries)
    {
        var ip = _currentUserContext.IpAddress;
        var ua = _currentUserContext.UserAgent;

        foreach (var auditEntry in auditEntries)
        {
            foreach (var prop in auditEntry.TemporaryProperties)
            {
                if (prop.Metadata.IsPrimaryKey())
                {
                    auditEntry.EntityId = prop.CurrentValue?.ToString() ?? string.Empty;
                }
                auditEntry.NewValues[prop.Metadata.Name] = prop.CurrentValue;
            }

            if (string.IsNullOrEmpty(auditEntry.EntityId))
            {
                var keyName = auditEntry.Entry.Metadata.FindPrimaryKey()?.Properties.Select(p => p.Name).FirstOrDefault();
                if (keyName != null)
                {
                    auditEntry.EntityId = auditEntry.Entry.Property(keyName).CurrentValue?.ToString() ?? string.Empty;
                }
            }

            var auditEvent = auditEntry.ToEvent(ip, ua);
            await _publishEndpoint.Publish(auditEvent);
        }
    }
}

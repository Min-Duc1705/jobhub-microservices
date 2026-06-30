using CommonService.Models.Interface;
using ResumeService.Models;
using Microsoft.EntityFrameworkCore;
using CommonService.Common;
using CommonService.Models;
using MassTransit;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace ResumeService.Data;

public class ResumeDbContext : DbContext
{
    private readonly ICurrentUserContext _currentUserContext;
    private readonly IPublishEndpoint _publishEndpoint;

    public ResumeDbContext(
        DbContextOptions<ResumeDbContext> options,
        ICurrentUserContext currentUserContext,
        IPublishEndpoint publishEndpoint) : base(options)
    {
        _currentUserContext = currentUserContext;
        _publishEndpoint = publishEndpoint;
    }

    // ── DbSets ────────────────────────────────────────────────────────────────
    public DbSet<Resume>      Resumes      { get; set; } = null!;
    public DbSet<Application> Applications { get; set; } = null!;
    public DbSet<Interview>   Interviews   { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ── Resume ────────────────────────────────────────────────────────────
        modelBuilder.Entity<Resume>(entity =>
        {
            entity.HasKey(r => r.Id);

            entity.Property(r => r.Title).IsRequired().HasMaxLength(300);
            entity.Property(r => r.Url).IsRequired(false).HasMaxLength(2000); // Null nếu là Online CV
            entity.Property(r => r.ContentJson).IsRequired(false);            // JSON không giới hạn length

            // Indexes phục vụ tìm kiếm và filter
            entity.HasIndex(r => r.CustomerId).HasDatabaseName("IX_Resumes_CustomerId");
            entity.HasIndex(r => r.IsDefault).HasDatabaseName("IX_Resumes_IsDefault");
            entity.HasIndex(r => r.IsDeleted).HasDatabaseName("IX_Resumes_IsDeleted");
            entity.HasIndex(r => r.IsOnlineCv).HasDatabaseName("IX_Resumes_IsOnlineCv");

            // Soft-delete query filter
            entity.HasQueryFilter(r => !r.IsDeleted);
        });

        // ── Application ───────────────────────────────────────────────────────
        modelBuilder.Entity<Application>(entity =>
        {
            entity.HasKey(a => a.Id);

            entity.Property(a => a.Status).HasConversion<string>();
            entity.Property(a => a.CoverLetter).HasMaxLength(10000);
            entity.Property(a => a.ReviewNote).HasMaxLength(5000);

            // FK nội bộ: Application → Resume
            entity.HasOne(a => a.Resume)
                  .WithMany(r => r.Applications)
                  .HasForeignKey(a => a.ResumeId)
                  .OnDelete(DeleteBehavior.Restrict); // Không xóa Resume nếu đang có Application dùng

            // Indexes
            entity.HasIndex(a => a.CustomerId).HasDatabaseName("IX_Applications_CustomerId");
            entity.HasIndex(a => a.JobId).HasDatabaseName("IX_Applications_JobId");
            entity.HasIndex(a => a.ResumeId).HasDatabaseName("IX_Applications_ResumeId");
            entity.HasIndex(a => a.Status).HasDatabaseName("IX_Applications_Status");
            entity.HasIndex(a => a.IsDeleted).HasDatabaseName("IX_Applications_IsDeleted");

            // Unique: mỗi ứng viên chỉ ứng tuyển 1 lần cho 1 Job
            entity.HasIndex(a => new { a.CustomerId, a.JobId })
                  .IsUnique()
                  .HasDatabaseName("IX_Applications_Customer_Job_Unique")
                  .HasFilter("\"IsDeleted\" = false");

            // Soft-delete query filter
            entity.HasQueryFilter(a => !a.IsDeleted);
        });

        // ── Interview ─────────────────────────────────────────────────────────
        modelBuilder.Entity<Interview>(entity =>
        {
            entity.HasKey(i => i.Id);

            entity.Property(i => i.Type).IsRequired().HasMaxLength(50);
            entity.Property(i => i.Status).IsRequired().HasMaxLength(50);
            entity.Property(i => i.MeetingLink).IsRequired(false).HasMaxLength(2000);
            entity.Property(i => i.Location).IsRequired(false).HasMaxLength(1000);
            entity.Property(i => i.Notes).IsRequired(false);

            // Indexes
            entity.HasIndex(i => i.JobId).HasDatabaseName("IX_Interviews_JobId");
            entity.HasIndex(i => i.CandidateId).HasDatabaseName("IX_Interviews_CandidateId");
            entity.HasIndex(i => i.RecruiterId).HasDatabaseName("IX_Interviews_RecruiterId");
            entity.HasIndex(i => i.IsDeleted).HasDatabaseName("IX_Interviews_IsDeleted");

            // Soft-delete query filter
            entity.HasQueryFilter(i => !i.IsDeleted);
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

using CommonService.Models.Interface;
using MassTransit;
using MassTransit.EntityFrameworkCoreIntegration;
using Microsoft.EntityFrameworkCore;
using ProfileService.Models;

namespace ProfileService.Data;

public class ProfileDbContext : DbContext
{
    public ProfileDbContext(DbContextOptions<ProfileDbContext> options) : base(options)
    {
    }

    // ── Domain DbSets ──────────────────────────────────────────────────────────
    public DbSet<Customer>     Customers     { get; set; } = null!;
    public DbSet<Skill>        Skills        { get; set; } = null!;
    public DbSet<CustomerSkill> CustomerSkills { get; set; } = null!;

    // ── MassTransit Outbox Tables ──────────────────────────────────────────────
    public DbSet<OutboxMessage> OutboxMessages { get; set; }
    public DbSet<OutboxState>   OutboxStates   { get; set; }
    public DbSet<InboxState>    InboxStates    { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ── Customer ───────────────────────────────────────────────────────────
        modelBuilder.Entity<Customer>(entity =>
        {
            entity.HasKey(c => c.Id);
            entity.HasIndex(c => c.AppUserId).IsUnique();

            entity.Property(c => c.Type).HasConversion<string>();
            entity.Property(c => c.Gender).HasConversion<string>();
            entity.Property(c => c.JobSearchStatus).HasConversion<string>();
        });

        // ── Skill (Replica) ────────────────────────────────────────────────────
        modelBuilder.Entity<Skill>(entity =>
        {
            entity.HasKey(s => s.Id);
        });

        // ── CustomerSkill (junction) ───────────────────────────────────────────
        modelBuilder.Entity<CustomerSkill>(entity =>
        {
            entity.HasKey(cs => new { cs.CustomerId, cs.SkillId });

            entity.HasOne(cs => cs.Customer)
                  .WithMany(c => c.CustomerSkills)
                  .HasForeignKey(cs => cs.CustomerId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(cs => cs.Skill)
                  .WithMany(s => s.CustomerSkills)
                  .HasForeignKey(cs => cs.SkillId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        // ── MassTransit Outbox/Inbox Tables ────────────────────────────────────
        modelBuilder.AddInboxStateEntity();
        modelBuilder.AddOutboxMessageEntity();
        modelBuilder.AddOutboxStateEntity();
    }

    // ── Tự động gán Audit Fields khi SaveChanges ──────────────────────────────
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

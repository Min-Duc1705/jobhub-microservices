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
    public DbSet<Conversation> Conversations { get; set; } = null!;
    public DbSet<Message> Messages { get; set; } = null!;
    public DbSet<Contact> Contacts { get; set; } = null!;
    public DbSet<HireAgentCampaign> HireAgentCampaigns { get; set; } = null!;
    public DbSet<HireAgentConversation> HireAgentConversations { get; set; } = null!;
    public DbSet<UserTelegramBinding> UserTelegramBindings { get; set; } = null!;
    public DbSet<UserCronSchedule> UserCronSchedules { get; set; } = null!;
    public DbSet<UserGoogleCredential> UserGoogleCredentials { get; set; } = null!;
    public DbSet<InterviewGoogleEvent> InterviewGoogleEvents { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<UserTelegramBinding>(entity =>
        {
            entity.HasKey(ut => ut.Id);
            entity.HasIndex(ut => ut.UserId).IsUnique().HasDatabaseName("IX_UserTelegramBindings_UserId");
            entity.HasIndex(ut => new { ut.TelegramChatId, ut.BotToken }).IsUnique().HasDatabaseName("IX_UserTelegramBindings_TelegramChatId_BotToken");
        });

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

        modelBuilder.Entity<Conversation>(entity =>
        {
            entity.HasKey(c => c.Id);
            entity.HasIndex(c => c.ParticipantA).HasDatabaseName("IX_Conversations_ParticipantA");
            entity.HasIndex(c => c.ParticipantB).HasDatabaseName("IX_Conversations_ParticipantB");
            entity.HasIndex(c => c.IsDeleted).HasDatabaseName("IX_Conversations_IsDeleted");
            entity.HasQueryFilter(c => !c.IsDeleted);
        });

        modelBuilder.Entity<Message>(entity =>
        {
            entity.HasKey(m => m.Id);
            entity.HasIndex(m => m.ConversationId).HasDatabaseName("IX_Messages_ConversationId");
            entity.HasIndex(m => m.SenderId).HasDatabaseName("IX_Messages_SenderId");
            entity.HasIndex(m => m.CreatedAt).HasDatabaseName("IX_Messages_CreatedAt");
            entity.HasIndex(m => m.IsDeleted).HasDatabaseName("IX_Messages_IsDeleted");
            entity.HasQueryFilter(m => !m.IsDeleted);

            entity.HasOne(m => m.Conversation)
                  .WithMany()
                  .HasForeignKey(m => m.ConversationId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<UserCronSchedule>(entity =>
        {
            entity.HasKey(s => s.Id);
            entity.HasIndex(s => s.UserId).HasDatabaseName("IX_UserCronSchedules_UserId");
            entity.HasIndex(s => s.TelegramChatId).HasDatabaseName("IX_UserCronSchedules_TelegramChatId");
            entity.HasIndex(s => new { s.IsActive, s.NextRunAt }).HasDatabaseName("IX_UserCronSchedules_Active_NextRun");
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

using AuthService.Models;
using CommonService.Models.Interface;
using MassTransit;
using MassTransit.EntityFrameworkCoreIntegration;
using Microsoft.EntityFrameworkCore;

namespace AuthService.Data;

public class AuthDbContext : DbContext
{
    public AuthDbContext(DbContextOptions<AuthDbContext> options) : base(options) { }

    // ── Domain DbSets ──────────────────────────────────────────────────────────
    public DbSet<AppUser>    AppUsers    => Set<AppUser>();
    public DbSet<Role>       Roles       => Set<Role>();
    public DbSet<Permission> Permissions => Set<Permission>();

    // ── MassTransit Outbox Tables ──────────────────────────────────────────────
    // Bảng lưu tạm Event chưa bắn được lên RabbitMQ (Outbox)
    public DbSet<OutboxMessage> OutboxMessages { get; set; }
    // Bảng theo dõi trạng thái Outbox của từng Task
    public DbSet<OutboxState>   OutboxStates   { get; set; }
    // Bảng đảm bảo Idempotency phía Consumer Service (tránh nhận Event 2 lần)
    public DbSet<InboxState>    InboxStates    { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ── AppUser ────────────────────────────────────────────────────────────
        modelBuilder.Entity<AppUser>(entity =>
        {
            entity.ToTable("AppUsers");
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.Email).IsUnique().HasDatabaseName("IX_Users_Email");
            
            // Thêm các index phục vụ truy vấn và filter
            entity.HasIndex(e => e.Username).HasDatabaseName("IX_Users_Username");
            entity.HasIndex(e => e.IsDeleted).HasDatabaseName("IX_Users_IsDeleted");
            entity.HasIndex(e => e.Status).HasDatabaseName("IX_Users_Status");

            entity.Property(e => e.Email).IsRequired().HasMaxLength(256);
            entity.Property(e => e.Username).IsRequired().HasMaxLength(50);
            entity.Property(e => e.PasswordHash).IsRequired();
            entity.Property(e => e.Status)
                  .HasConversion<string>(); // Lưu Enum dạng string: "Active", "Pending"...

            // AppUser N-1 Role — xóa Role không xóa User (SetNull)
            entity.HasOne(u => u.Role)
                  .WithMany(r => r.Users)
                  .HasForeignKey(u => u.RoleId)
                  .OnDelete(DeleteBehavior.SetNull);
        });

        // ── Role ───────────────────────────────────────────────────────────────
        modelBuilder.Entity<Role>(entity =>
        {
            entity.ToTable("Roles");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(100);
            entity.HasIndex(e => e.Name).IsUnique().HasDatabaseName("IX_Roles_Name");
            entity.HasIndex(e => e.IsDeleted).HasDatabaseName("IX_Roles_IsDeleted"); // Index soft-delete

            // Role M-N Permission — EF tự tạo bảng trung gian
            entity.HasMany(r => r.Permissions)
                  .WithMany(p => p.Roles)
                  .UsingEntity(j => j.ToTable("RolePermissions"));
        });

        // ── Permission ─────────────────────────────────────────────────────────
        modelBuilder.Entity<Permission>(entity =>
        {
            entity.ToTable("Permissions");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(200);
            entity.Property(e => e.ApiPath).IsRequired().HasMaxLength(500);
            entity.Property(e => e.Method).IsRequired().HasMaxLength(10);
            entity.Property(e => e.Module).IsRequired().HasMaxLength(100);

            // Composite unique: cùng path + method chỉ tồn tại 1 lần
            entity.HasIndex(e => new { e.ApiPath, e.Method })
                  .IsUnique()
                  .HasDatabaseName("IX_Permissions_Path_Method");
                  
            // Thêm index cho filter theo Module
            entity.HasIndex(e => e.Module).HasDatabaseName("IX_Permissions_Module");
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

        // TODO: Inject IHttpContextAccessor để lấy UserId thật từ JWT claim
        var currentUser = "system";

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

        return base.SaveChangesAsync(cancellationToken);
    }
}

using CommonService.Models.Interface;
using Microsoft.EntityFrameworkCore;
using CompanyService.Models;

namespace CompanyService.Data;

public class CompanyDbContext : DbContext
{
    public CompanyDbContext(DbContextOptions<CompanyDbContext> options) : base(options) { }

    // ── DbSets ────────────────────────────────────────────────────────────────
    public DbSet<Company> Companies { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ── Company ───────────────────────────────────────────────────────────
        modelBuilder.Entity<Company>(entity =>
        {
            entity.HasKey(c => c.Id);

            entity.HasIndex(c => c.TaxCode)
                  .IsUnique()
                  .HasFilter("\"TaxCode\" IS NOT NULL");  // Partial unique — cho phép nhiều NULL
                  
            // Thêm các index phục vụ truy vấn và filter tìm kiếm
            entity.HasIndex(c => c.Name).HasDatabaseName("IX_Companies_Name");
            entity.HasIndex(c => c.Industry).HasDatabaseName("IX_Companies_Industry");
            entity.HasIndex(c => c.CompanySize).HasDatabaseName("IX_Companies_CompanySize");
            entity.HasIndex(c => c.IsVerified).HasDatabaseName("IX_Companies_IsVerified");
            entity.HasIndex(c => c.IsDeleted).HasDatabaseName("IX_Companies_IsDeleted");

            entity.Property(c => c.CompanySize)
                  .HasConversion<string>();

            // Lưu List<string> ActivityImages dưới dạng JSON column
            // Phải dùng static method vì EF expression tree không nhận lambda có statement body
            entity.Property(c => c.ActivityImages)
                  .HasColumnType("jsonb")
                  .HasConversion(
                      v => SerializeImages(v),
                      v => DeserializeImages(v)
                  )
                  .Metadata.SetValueComparer(new Microsoft.EntityFrameworkCore.ChangeTracking.ValueComparer<List<string>>(
                      (c1, c2) => c1!.SequenceEqual(c2!),
                      c => c.Aggregate(0, (a, v) => HashCode.Combine(a, v.GetHashCode())),
                      c => c.ToList()
                  ));

            entity.Property(c => c.Name)
                  .IsRequired()
                  .HasMaxLength(200);

            entity.Property(c => c.ContactEmail)
                  .HasMaxLength(200);

            entity.Property(c => c.Website)
                  .HasMaxLength(500);

            entity.Property(c => c.TaxCode)
                  .HasMaxLength(50);

            // Soft-delete: mặc định chỉ query bản ghi chưa xoá
            entity.HasQueryFilter(c => !c.IsDeleted);
        });
    }

    // ── JSON helpers (static để dùng trong EF expression tree) ────────────────

    private static string SerializeImages(List<string> v)
        => System.Text.Json.JsonSerializer.Serialize(v, (System.Text.Json.JsonSerializerOptions?)null);

    private static List<string> DeserializeImages(string v)
    {
        if (string.IsNullOrWhiteSpace(v) || v == "{}" || v == "null" || v == "\"\"")
            return new List<string>();
        try
        {
            return System.Text.Json.JsonSerializer
                       .Deserialize<List<string>>(v, (System.Text.Json.JsonSerializerOptions?)null)
                   ?? new List<string>();
        }
        catch
        {
            return new List<string>();
        }
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

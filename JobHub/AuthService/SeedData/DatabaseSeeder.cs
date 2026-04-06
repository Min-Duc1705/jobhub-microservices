using AuthService.Data;
using AuthService.Models;
using Microsoft.EntityFrameworkCore;

namespace AuthService.SeedData;

/// <summary>
/// Seed toàn bộ Permissions, Roles và Admin user ban đầu.
/// Chạy tự động khi app khởi động. Idempotent — an toàn chạy nhiều lần.
/// </summary>
public static class DatabaseSeeder
{
    public static async Task SeedAsync(AuthDbContext context)
    {
        // ── 1. Seed Permissions ────────────────────────────────────────────────
        if (!await context.Permissions.AnyAsync())
        {
            var permissions = GetAllPermissions();
            await context.Permissions.AddRangeAsync(permissions);
            await context.SaveChangesAsync();
            Console.WriteLine($"[Seeder] ✅ Đã tạo {permissions.Count} Permissions.");
        }

        // ── 2. Seed Roles ──────────────────────────────────────────────────────
        if (!await context.Roles.AnyAsync())
        {
            var allPerms = await context.Permissions.ToListAsync();
            var permDict = allPerms.ToDictionary(p => $"{p.Method}:{p.ApiPath}");

            var roles = BuildRoles(permDict);
            await context.Roles.AddRangeAsync(roles);
            await context.SaveChangesAsync();
            Console.WriteLine($"[Seeder] ✅ Đã tạo {roles.Count} Roles: ADMIN, HR, CANDIDATE.");
        }

        // ── 3. Seed Admin user ─────────────────────────────────────────────────
        if (!await context.AppUsers.AnyAsync())
        {
            var adminRole = await context.Roles.FirstOrDefaultAsync(r => r.Name == "ADMIN");
            if (adminRole != null)
            {
                var admin = new AppUser
                {
                    Email        = "admin@jobhub.vn",
                    PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin@123456"),
                    Status       = UserStatus.Active,
                    RoleId       = adminRole.Id,
                };
                await context.AppUsers.AddAsync(admin);
                await context.SaveChangesAsync();
                Console.WriteLine("[Seeder] ✅ Đã tạo tài khoản Admin mặc định.");
                Console.WriteLine("[Seeder]    Email: admin@jobhub.vn | Password: Admin@123456");
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Danh sách toàn bộ Permissions của hệ thống JobHub
    // ─────────────────────────────────────────────────────────────────────────
    private static List<Permission> GetAllPermissions() => new()
    {
        // ── AUTH ─────────────────────────────────────────────────────────────
        new() { Name = "Xem thông tin tài khoản",          ApiPath = "/api/v1/auth/account",              Method = "GET",    Module = "AUTH" },

        // ── USER ─────────────────────────────────────────────────────────────
        new() { Name = "Xem danh sách user",               ApiPath = "/api/v1/users",                     Method = "GET",    Module = "USER" },
        new() { Name = "Xem chi tiết user",                ApiPath = "/api/v1/users/{id}",                Method = "GET",    Module = "USER" },
        new() { Name = "Tạo user mới",                     ApiPath = "/api/v1/users",                     Method = "POST",   Module = "USER" },
        new() { Name = "Cập nhật user",                    ApiPath = "/api/v1/users/{id}",                Method = "PUT",    Module = "USER" },
        new() { Name = "Xóa user",                         ApiPath = "/api/v1/users/{id}",                Method = "DELETE", Module = "USER" },
        new() { Name = "Đặt lại mật khẩu user",           ApiPath = "/api/v1/users/{id}/reset-password", Method = "PATCH",  Module = "USER" },

        // ── ROLE ─────────────────────────────────────────────────────────────
        new() { Name = "Xem danh sách role",               ApiPath = "/api/v1/roles",                     Method = "GET",    Module = "ROLE" },
        new() { Name = "Xem chi tiết role",                ApiPath = "/api/v1/roles/{id}",                Method = "GET",    Module = "ROLE" },
        new() { Name = "Tạo role mới",                     ApiPath = "/api/v1/roles",                     Method = "POST",   Module = "ROLE" },
        new() { Name = "Cập nhật role",                    ApiPath = "/api/v1/roles/{id}",                Method = "PUT",    Module = "ROLE" },
        new() { Name = "Xóa role",                         ApiPath = "/api/v1/roles/{id}",                Method = "DELETE", Module = "ROLE" },

        // ── PERMISSION ───────────────────────────────────────────────────────
        new() { Name = "Xem danh sách permission",         ApiPath = "/api/v1/permissions",               Method = "GET",    Module = "PERMISSION" },
        new() { Name = "Xem chi tiết permission",          ApiPath = "/api/v1/permissions/{id}",          Method = "GET",    Module = "PERMISSION" },
        new() { Name = "Tạo permission mới",               ApiPath = "/api/v1/permissions",               Method = "POST",   Module = "PERMISSION" },
        new() { Name = "Cập nhật permission",              ApiPath = "/api/v1/permissions/{id}",          Method = "PUT",    Module = "PERMISSION" },
        new() { Name = "Xóa permission",                   ApiPath = "/api/v1/permissions/{id}",          Method = "DELETE", Module = "PERMISSION" },

        // ── PROFILE SERVICE ──────────────────────────────────────────────────
        new() { Name = "Xem danh sách hồ sơ",             ApiPath = "/api/v1/customers",                 Method = "GET",    Module = "PROFILE" },
        new() { Name = "Xem hồ sơ theo ID",               ApiPath = "/api/v1/customers/{id}",            Method = "GET",    Module = "PROFILE" },

        // ── SKILL ────────────────────────────────────────────────────────────
        new() { Name = "Xem danh sách kỹ năng (Admin)",   ApiPath = "/api/v1/skills",                    Method = "GET",    Module = "SKILL" },
        new() { Name = "Tạo kỹ năng mới",                 ApiPath = "/api/v1/skills",                    Method = "POST",   Module = "SKILL" },
        new() { Name = "Cập nhật kỹ năng",                ApiPath = "/api/v1/skills/{id}",               Method = "PUT",    Module = "SKILL" },
        new() { Name = "Xóa kỹ năng",                     ApiPath = "/api/v1/skills/{id}",               Method = "DELETE", Module = "SKILL" },
    };

    // ─────────────────────────────────────────────────────────────────────────
    // Xây dựng 3 Roles + gán Permissions tương ứng
    // ─────────────────────────────────────────────────────────────────────────
    private static List<Role> BuildRoles(Dictionary<string, Permission> perms)
    {
        Permission Get(string method, string path) =>
            perms.TryGetValue($"{method}:{path}", out var p) ? p
            : throw new Exception($"[Seeder] Permission không tồn tại: {method} {path}");

        // ── ADMIN — toàn quyền ───────────────────────────────────────────────
        var admin = new Role
        {
            Name        = "ADMIN",
            Description = "Quản trị viên hệ thống — toàn quyền",
            Active      = true,
            Permissions = perms.Values.ToList()  // gán tất cả
        };

        // ── HR — Nhà tuyển dụng ──────────────────────────────────────────────
        var hr = new Role
        {
            Name        = "HR",
            Description = "Nhà tuyển dụng — xem CV ứng viên, đăng tin tuyển dụng",
            Active      = true,
            Permissions = new List<Permission>
            {
                Get("GET", "/api/v1/auth/account"),
                Get("GET", "/api/v1/customers/{id}"),
                Get("GET", "/api/v1/customers"),
                Get("GET", "/api/v1/skills"),
            }
        };

        // ── CANDIDATE — Ứng viên ─────────────────────────────────────────────
        var candidate = new Role
        {
            Name        = "CANDIDATE",
            Description = "Ứng viên — tìm việc, nộp CV, cập nhật hồ sơ",
            Active      = true,
            Permissions = new List<Permission>
            {
                Get("GET", "/api/v1/auth/account"),
            }
        };

        return new List<Role> { admin, hr, candidate };
    }
}

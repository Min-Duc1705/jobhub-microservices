using AuthService.Data;
using AuthService.Models;
using CommonService.Caching;
using Microsoft.EntityFrameworkCore;

namespace AuthService.SeedData;

/// <summary>
/// Seed toàn bộ Permissions, Roles và Admin user ban đầu.
/// Chạy tự động khi app khởi động. Idempotent — an toàn chạy nhiều lần.
/// </summary>
public static class DatabaseSeeder
{
    public static async Task SeedAsync(AuthDbContext context, ICacheService cacheService)
    {
        const string CACHE_KEY_DROPDOWN = "permissions:dropdown";

        // ── 1. Upsert Permissions ──────────────────────────────────────────────
        var allDefined = GetAllPermissions();

        var existing = await context.Permissions
            .Select(p => new { p.Method, p.ApiPath })
            .ToListAsync();
        var existingKeys = existing
            .Select(p => $"{p.Method}:{p.ApiPath}")
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        var toAdd = allDefined
            .Where(p => !existingKeys.Contains($"{p.Method}:{p.ApiPath}"))
            .ToList();

        if (toAdd.Count > 0)
        {
            await context.Permissions.AddRangeAsync(toAdd);
            await context.SaveChangesAsync();
            await cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);
            Console.WriteLine($"[Seeder] ✅ Đã thêm {toAdd.Count} Permissions mới & xóa cache dropdown.");
        }
        else
        {
            Console.WriteLine("[Seeder] ℹ️  Tất cả Permissions đã tồn tại, bỏ qua.");
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
        else
        {
            // Cập nhật ADMIN role để luôn có đủ tất cả permissions
            var adminRole = await context.Roles
                .Include(r => r.Permissions)
                .FirstOrDefaultAsync(r => r.Name == "ADMIN");

            if (adminRole != null)
            {
                var allPerms = await context.Permissions.ToListAsync();
                var missing = allPerms
                    .Where(p => !adminRole.Permissions.Any(rp => rp.Id == p.Id))
                    .ToList();

                if (missing.Count > 0)
                {
                    foreach (var p in missing)
                        adminRole.Permissions.Add(p);
                    await context.SaveChangesAsync();
                    Console.WriteLine($"[Seeder] ✅ Đã bổ sung {missing.Count} Permissions mới cho ADMIN role.");
                }
            }

            // Loại bỏ permission broadcast khỏi HR role nếu có
            var hrRole = await context.Roles
                .Include(r => r.Permissions)
                .FirstOrDefaultAsync(r => r.Name == "HR");

            if (hrRole != null)
            {
                var broadcastPerm = hrRole.Permissions
                    .FirstOrDefault(p => p.Method == "POST" && p.ApiPath == "/api/v1/users/notifications/broadcast");

                if (broadcastPerm != null)
                {
                    hrRole.Permissions.Remove(broadcastPerm);
                    await context.SaveChangesAsync();
                    Console.WriteLine("[Seeder] ℹ️ Đã gỡ bỏ permission broadcast khỏi HR role.");
                }
            }
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
        new() { Name = "Gửi thông báo broadcast",          ApiPath = "/api/v1/users/notifications/broadcast", Method = "POST", Module = "USER" },
        new() { Name = "Import danh sách user",            ApiPath = "/api/v1/users/import",              Method = "POST",   Module = "USER" },

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
        new() { Name = "Cập nhật hồ sơ cá nhân",          ApiPath = "/api/v1/customers/me",              Method = "PUT",    Module = "PROFILE" },

        // ── SKILL ────────────────────────────────────────────────────────────
        new() { Name = "Xem danh sách kỹ năng (Admin)",   ApiPath = "/api/v1/skills",                    Method = "GET",    Module = "SKILL" },
        new() { Name = "Tạo kỹ năng mới",                 ApiPath = "/api/v1/skills",                    Method = "POST",   Module = "SKILL" },
        new() { Name = "Cập nhật kỹ năng",                ApiPath = "/api/v1/skills/{id}",               Method = "PUT",    Module = "SKILL" },
        new() { Name = "Xóa kỹ năng",                     ApiPath = "/api/v1/skills/{id}",               Method = "DELETE", Module = "SKILL" },
        new() { Name = "Import danh sách kỹ năng",         ApiPath = "/api/v1/skills/import",             Method = "POST",   Module = "SKILL" },

        // ── COMPANY SERVICE ───────────────────────────────────────────────────
        new() { Name = "Xem danh sách công ty",            ApiPath = "/api/v1/companies",                 Method = "GET",    Module = "COMPANY" },
        new() { Name = "Xem chi tiết công ty",             ApiPath = "/api/v1/companies/{id}",            Method = "GET",    Module = "COMPANY" },
        new() { Name = "Tạo công ty mới",                  ApiPath = "/api/v1/companies",                 Method = "POST",   Module = "COMPANY" },
        new() { Name = "Cập nhật thông tin công ty",       ApiPath = "/api/v1/companies/{id}",            Method = "PUT",    Module = "COMPANY" },
        new() { Name = "Xóa công ty",                      ApiPath = "/api/v1/companies/{id}",            Method = "DELETE", Module = "COMPANY" },
        new() { Name = "Xác minh công ty",                 ApiPath = "/api/v1/companies/{id}/verify",     Method = "PATCH",  Module = "COMPANY" },
        new() { Name = "Import danh sách công ty",          ApiPath = "/api/v1/companies/import",          Method = "POST",   Module = "COMPANY" },

        // ── JOB SERVICE ───────────────────────────────────────────────────────
        new() { Name = "Xem danh sách tin tuyển dụng",     ApiPath = "/api/v1/jobs",                      Method = "GET",    Module = "JOB" },
        new() { Name = "Xem chi tiết tin tuyển dụng",      ApiPath = "/api/v1/jobs/{id}",                 Method = "GET",    Module = "JOB" },
        new() { Name = "Tạo tin tuyển dụng",               ApiPath = "/api/v1/jobs",                      Method = "POST",   Module = "JOB" },
        new() { Name = "Cập nhật tin tuyển dụng",          ApiPath = "/api/v1/jobs/{id}",                 Method = "PUT",    Module = "JOB" },
        new() { Name = "Xóa tin tuyển dụng",               ApiPath = "/api/v1/jobs/{id}",                 Method = "DELETE", Module = "JOB" },
        new() { Name = "Đổi trạng thái tin tuyển dụng",    ApiPath = "/api/v1/jobs/{id}/status",          Method = "PATCH",  Module = "JOB" },
        new() { Name = "Import danh sách tin tuyển dụng",   ApiPath = "/api/v1/admin/jobs/import",         Method = "POST",   Module = "JOB" },

        // ── SAVED JOBS ────────────────────────────────────────────────────────
        new() { Name = "Xem danh sách việc làm đã lưu",    ApiPath = "/api/v1/saved-jobs",                Method = "GET",    Module = "JOB" },
        new() { Name = "Lưu tin tuyển dụng",                ApiPath = "/api/v1/saved-jobs/{jobId}",       Method = "POST",   Module = "JOB" },
        new() { Name = "Bỏ lưu tin tuyển dụng",            ApiPath = "/api/v1/saved-jobs/{jobId}",        Method = "DELETE", Module = "JOB" },

        // ── RESUME SERVICE ────────────────────────────────────────────────────
        new() { Name = "Xem danh sách CV",              ApiPath = "/api/v1/resumes",                     Method = "GET",    Module = "RESUME" },
        new() { Name = "Xem chi tiết CV",               ApiPath = "/api/v1/resumes/{id}",                Method = "GET",    Module = "RESUME" },
        new() { Name = "Tải lên CV (file)",             ApiPath = "/api/v1/resumes",                     Method = "POST",   Module = "RESUME" },
        new() { Name = "Tạo CV Online (Builder)",       ApiPath = "/api/v1/resumes/online",              Method = "POST",   Module = "RESUME" },
        new() { Name = "Cập nhật thông tin CV",          ApiPath = "/api/v1/resumes/{id}",                Method = "PUT",    Module = "RESUME" },
        new() { Name = "Lưu nội dung CV Online",        ApiPath = "/api/v1/resumes/{id}/content",        Method = "PUT",    Module = "RESUME" },
        new() { Name = "Xóa CV",                        ApiPath = "/api/v1/resumes/{id}",                Method = "DELETE", Module = "RESUME" },
        new() { Name = "Đặt CV mặc định",               ApiPath = "/api/v1/resumes/{id}/set-default",    Method = "PATCH",  Module = "RESUME" },

        // ── APPLICATION SERVICE ───────────────────────────────────────────────
        new() { Name = "Xem danh sách đơn ứng tuyển",  ApiPath = "/api/v1/applications",                Method = "GET",    Module = "APPLICATION" },
        new() { Name = "Xem chi tiết đơn ứng tuyển",   ApiPath = "/api/v1/applications/{id}",           Method = "GET",    Module = "APPLICATION" },
        new() { Name = "Nộp đơn ứng tuyển",             ApiPath = "/api/v1/applications",                Method = "POST",   Module = "APPLICATION" },
        new() { Name = "Hủy đơn ứng tuyển",             ApiPath = "/api/v1/applications/{id}",           Method = "DELETE", Module = "APPLICATION" },
        new() { Name = "Cập nhật trạng thái đơn ứng tuyển", ApiPath = "/api/v1/applications/{id}/status", Method = "PATCH",  Module = "APPLICATION" },
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
            Permissions = perms.Values.ToList()
        };

        // ── HR — Nhà tuyển dụng ──────────────────────────────────────────────
        var hr = new Role
        {
            Name        = "HR",
            Description = "Nhà tuyển dụng — xem CV ứng viên, đăng tin tuyển dụng",
            Active      = true,
            Permissions = new List<Permission>
            {
                Get("GET",    "/api/v1/auth/account"),
                Get("GET",    "/api/v1/customers"),
                Get("GET",    "/api/v1/customers/{id}"),
                Get("GET",    "/api/v1/skills"),
                // Company
                Get("GET",    "/api/v1/companies"),
                Get("GET",    "/api/v1/companies/{id}"),
                Get("POST",   "/api/v1/companies"),
                Get("PUT",    "/api/v1/companies/{id}"),
                // Job: HR đăng và quản lý tin
                Get("GET",    "/api/v1/jobs"),
                Get("GET",    "/api/v1/jobs/{id}"),
                Get("POST",   "/api/v1/jobs"),
                Get("PUT",    "/api/v1/jobs/{id}"),
                Get("DELETE", "/api/v1/jobs/{id}"),
                Get("PATCH",  "/api/v1/jobs/{id}/status"),
                // Resume: HR xem CV ứng viên
                Get("GET",    "/api/v1/resumes"),
                Get("GET",    "/api/v1/resumes/{id}"),
                // Application: HR duyệt / từ chối đơn
                Get("GET",    "/api/v1/applications"),
                Get("GET",    "/api/v1/applications/{id}"),
                Get("PATCH",  "/api/v1/applications/{id}/status"),
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
                Get("GET",    "/api/v1/auth/account"),
                // Company: chỉ xem
                Get("GET",    "/api/v1/companies"),
                Get("GET",    "/api/v1/companies/{id}"),
                // Job: xem và lưu
                Get("GET",    "/api/v1/jobs"),
                Get("GET",    "/api/v1/jobs/{id}"),
                Get("GET",    "/api/v1/saved-jobs"),
                Get("POST",   "/api/v1/saved-jobs/{jobId}"),
                Get("DELETE", "/api/v1/saved-jobs/{jobId}"),
                // Resume: toàn quyền trên CV của bản thân
                Get("GET",    "/api/v1/resumes"),
                Get("GET",    "/api/v1/resumes/{id}"),
                Get("POST",   "/api/v1/resumes"),
                Get("POST",   "/api/v1/resumes/online"),
                Get("PUT",    "/api/v1/resumes/{id}"),
                Get("PUT",    "/api/v1/resumes/{id}/content"),
                Get("DELETE", "/api/v1/resumes/{id}"),
                Get("PATCH",  "/api/v1/resumes/{id}/set-default"),
                // Application: ứng viên nộp đơn, theo dõi và hủy
                Get("GET",    "/api/v1/applications"),
                Get("GET",    "/api/v1/applications/{id}"),
                Get("POST",   "/api/v1/applications"),
                Get("DELETE", "/api/v1/applications/{id}"),
                // Profile: cập nhật hồ sơ bản thân
                Get("PUT",    "/api/v1/customers/me"),
            }
        };

        return new List<Role> { admin, hr, candidate };
    }
}

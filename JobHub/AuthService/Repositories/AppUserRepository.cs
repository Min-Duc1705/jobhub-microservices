using AuthService.Data;
using AuthService.Models;
using AuthService.Repositories.Interface;
using CommonService.Repository;
using Microsoft.EntityFrameworkCore;

namespace AuthService.Repositories
{
    public class AppUserRepository : GenericRepository<AuthDbContext, AppUser>, IAppUserRepository
    {
        public AppUserRepository(AuthDbContext context) : base(context) { }

        /// <summary>Tìm theo email hoặc username, include Role + Permissions.</summary>
        public async Task<AppUser?> GetByEmailAsync(string emailOrUsername)
        {
            return await _context.AppUsers
                .Include(u => u.Role)
                    .ThenInclude(r => r!.Permissions)
                .FirstOrDefaultAsync(u =>
                    u.Email.ToLower()    == emailOrUsername.ToLower() ||
                    u.Email.ToLower()    == emailOrUsername.ToLower());
            // Note: AppUser không có Username (chỉ Email) — nếu cần thì thêm Username sau
        }

        public async Task<AppUser?> GetByRefreshTokenAsync(string refreshToken)
        {
            return await _context.AppUsers
                .Include(u => u.Role)
                    .ThenInclude(r => r!.Permissions)
                .FirstOrDefaultAsync(u => u.RefreshToken == refreshToken);
        }

        public async Task<bool> EmailExistsAsync(string email)
        {
            return await _context.AppUsers
                .IgnoreQueryFilters()
                .AnyAsync(u => u.Email.ToLower() == email.ToLower());
        }

        public async Task<List<AppUser>> GetUsersByRoleAsync(string roleName)
        {
            if (string.Equals(roleName, "ALL", StringComparison.OrdinalIgnoreCase))
            {
                return await _context.AppUsers
                    .Where(u => !u.IsDeleted)
                    .ToListAsync();
            }

            return await _context.AppUsers
                .Include(u => u.Role)
                .Where(u => u.Role != null && u.Role.Name.ToUpper() == roleName.ToUpper() && !u.IsDeleted)
                .ToListAsync();
        }
    }
}

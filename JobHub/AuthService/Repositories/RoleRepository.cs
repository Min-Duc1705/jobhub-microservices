using AuthService.Data;
using AuthService.Models;
using AuthService.Repositories.Interface;
using CommonService.Repository;
using Microsoft.EntityFrameworkCore;

namespace AuthService.Repositories
{
    public class RoleRepository : GenericRepository<AuthDbContext, Role>, IRoleRepository
    {
        public RoleRepository(AuthDbContext context) : base(context) { }

        public async Task<Role?> GetByNameAsync(string name)
        {
            return await _context.Roles
                .Include(r => r.Permissions)
                .AsNoTracking()
                .FirstOrDefaultAsync(r => r.Name.ToLower() == name.ToLower());
        }

        /// <summary>Tracking — để EF có thể phát hiện thay đổi collection M-N khi Update.</summary>
        public async Task<Role?> GetWithPermissionsAsync(Guid roleId)
        {
            return await _context.Roles
                .Include(r => r.Permissions)
                .FirstOrDefaultAsync(r => r.Id == roleId);
        }

        public async Task<List<Role>> GetAllDropdownAsync()
        {
            return await _context.Roles
                .AsNoTracking()
                .Where(r => r.Active && !r.IsDeleted)
                .OrderBy(r => r.Name)
                .Select(r => new Role { Id = r.Id, Name = r.Name })
                .ToListAsync();
        }

        public async Task<List<string>> GetUserEmailsByRoleIdAsync(Guid roleId)
        {
            return await _context.AppUsers
                .AsNoTracking()
                .Where(u => u.RoleId == roleId)
                .Select(u => u.Email)
                .ToListAsync();
        }
    }
}

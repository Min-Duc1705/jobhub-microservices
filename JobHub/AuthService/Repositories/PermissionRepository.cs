using AuthService.Data;
using AuthService.Models;
using AuthService.Repositories.Interface;
using CommonService.Repository;
using Microsoft.EntityFrameworkCore;

namespace AuthService.Repositories
{
    public class PermissionRepository : GenericRepository<AuthDbContext, Permission>, IPermissionRepository
    {
        public PermissionRepository(AuthDbContext context) : base(context) { }

        public async Task<Permission?> GetByPathAndMethodAsync(string apiPath, string method)
        {
            return await _context.Permissions
                .AsNoTracking()
                .FirstOrDefaultAsync(p =>
                    p.ApiPath.ToLower() == apiPath.ToLower() &&
                    p.Method.ToUpper()  == method.ToUpper());
        }

        public async Task<List<Permission>> GetPermissionsByIdsAsync(IEnumerable<Guid> ids)
        {
            var result = new List<Permission>();
            foreach (var id in ids)
            {
                // FindAsync check local cache trước rồi mới xuống DB
                var perm = await _context.Set<Permission>().FindAsync(id);
                if (perm != null) result.Add(perm);
            }
            return result;
        }

        public async Task<IEnumerable<Permission>> GetByModuleAsync(string module)
        {
            return await _context.Permissions
                .Where(p => p.Module.ToLower() == module.ToLower())
                .OrderBy(p => p.Name)
                .ToListAsync();
        }

        public async Task<IEnumerable<Permission>> GetAllDropdownAsync()
        {
            return await _context.Permissions
                .AsNoTracking()
                .Where(p => !p.IsDeleted)
                .OrderBy(p => p.Module)
                .ThenBy(p => p.Name)
                .ToListAsync();
        }
    }
}

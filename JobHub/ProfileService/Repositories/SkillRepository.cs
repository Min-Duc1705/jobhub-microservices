using CommonService.Repository;
using Microsoft.EntityFrameworkCore;
using ProfileService.Data;
using ProfileService.Models;
using ProfileService.Repositories.Interface;

namespace ProfileService.Repositories;

public class SkillRepository : GenericRepository<ProfileDbContext, Skill>, ISkillRepository
{
    public SkillRepository(ProfileDbContext context) : base(context)
    {
    }

    public async Task<Skill?> GetByNameAsync(string name)
        => await _dbSet.FirstOrDefaultAsync(s => s.Name.ToLower() == name.ToLower() && !s.IsDeleted);
}

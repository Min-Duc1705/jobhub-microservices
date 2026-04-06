using CommonService.Repository;
using Microsoft.EntityFrameworkCore;
using ProfileService.Data;
using ProfileService.Models;
using ProfileService.Repositories.Interface;

namespace ProfileService.Repositories;

public class CustomerRepository : GenericRepository<ProfileDbContext, Customer>, ICustomerRepository
{
    public CustomerRepository(ProfileDbContext dbContext) : base(dbContext)
    {
    }

    public async Task<Customer?> GetByAppUserIdAsync(Guid appUserId)
    {
        return await _dbSet
            .Include(c => c.CustomerSkills)
            .ThenInclude(cs => cs.Skill)
            .FirstOrDefaultAsync(c => c.AppUserId == appUserId && !c.IsDeleted);
    }
}

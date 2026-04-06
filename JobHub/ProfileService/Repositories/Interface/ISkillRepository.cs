using CommonService.Repository;
using ProfileService.Models;

namespace ProfileService.Repositories.Interface;

public interface ISkillRepository : IGenericRepository<Skill>
{
    Task<Skill?> GetByNameAsync(string name);
}

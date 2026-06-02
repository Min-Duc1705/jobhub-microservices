using CommonService.Repository;
using JobService.Models;

namespace JobService.Repositories.Interface;

public interface IJobRepository : IGenericRepository<Job>
{
    /// <summary>Tăng ViewCount lên 1 (optimistic, không cần load entity).</summary>
    Task IncrementViewCountAsync(Guid jobId);

    /// <summary>Lấy thông tin Job và danh sách JobSkills với cơ chế Tracking của EF Core.</summary>
    Task<Job?> GetJobWithSkillsTrackedAsync(Guid id);
}

public interface ISkillRepository : IGenericRepository<Skill>
{
    Task<Skill?> GetByNameAsync(string name);
    Task<List<Skill>> GetByIdsAsync(IEnumerable<Guid> ids);
}

public interface ISavedJobRepository
{
    Task<SavedJob?> GetAsync(Guid jobId, Guid customerId);
    Task<List<SavedJob>> GetByCustomerAsync(Guid customerId, int pageNumber, int pageSize);
    Task<int> CountByCustomerAsync(Guid customerId);
    Task AddAsync(SavedJob savedJob);
    void Delete(SavedJob savedJob);
    Task SaveChangesAsync();
}

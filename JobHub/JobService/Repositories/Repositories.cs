using CommonService.Repository;
using JobService.Data;
using JobService.Models;
using JobService.Repositories.Interface;
using Microsoft.EntityFrameworkCore;

namespace JobService.Repositories;

public class JobRepository : GenericRepository<JobDbContext, Job>, IJobRepository
{
    public JobRepository(JobDbContext context) : base(context) { }

    public async Task IncrementViewCountAsync(Guid jobId)
        => await _dbSet
            .Where(j => j.Id == jobId)
            .ExecuteUpdateAsync(s => s.SetProperty(j => j.ViewCount, j => j.ViewCount + 1));

    public async Task<Job?> GetJobWithSkillsTrackedAsync(Guid id)
        => await _dbSet
            .Include(j => j.JobSkills)
            .ThenInclude(js => js.Skill)
            .FirstOrDefaultAsync(j => j.Id == id && !j.IsDeleted);
}

public class SkillRepository : GenericRepository<JobDbContext, Skill>, ISkillRepository
{
    public SkillRepository(JobDbContext context) : base(context) { }

    public async Task<Skill?> GetByNameAsync(string name)
        => await _dbSet.FirstOrDefaultAsync(s => s.Name.ToLower() == name.ToLower() && !s.IsDeleted);

    public async Task<List<Skill>> GetByIdsAsync(IEnumerable<Guid> ids)
        => await _dbSet.Where(s => ids.Contains(s.Id) && !s.IsDeleted).ToListAsync();
}

public class SavedJobRepository : ISavedJobRepository
{
    private readonly JobDbContext _context;

    public SavedJobRepository(JobDbContext context) => _context = context;

    public async Task<SavedJob?> GetAsync(Guid jobId, Guid customerId)
        => await _context.SavedJobs
            .Include(sv => sv.Job)
            .FirstOrDefaultAsync(sv => sv.JobId == jobId && sv.CustomerId == customerId);

    public async Task<List<SavedJob>> GetByCustomerAsync(Guid customerId, int pageNumber, int pageSize)
        => await _context.SavedJobs
            .Include(sv => sv.Job).ThenInclude(j => j.JobSkills)
            .Where(sv => sv.CustomerId == customerId)
            .OrderByDescending(sv => sv.SavedAt)
            .Skip((pageNumber - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

    public async Task<int> CountByCustomerAsync(Guid customerId)
        => await _context.SavedJobs
            .CountAsync(sv => sv.CustomerId == customerId);

    public async Task AddAsync(SavedJob savedJob)
        => await _context.SavedJobs.AddAsync(savedJob);

    public void Delete(SavedJob savedJob)
        => _context.SavedJobs.Remove(savedJob);

    public async Task SaveChangesAsync()
        => await _context.SaveChangesAsync();
}

using CommonService.Repository;
using CommonService.Specifications;
using Microsoft.EntityFrameworkCore;
using ResumeService.Data;
using ResumeService.Models;
using ResumeService.Repositories.Interface;

namespace ResumeService.Repositories;

public class ApplicationRepository : GenericRepository<ResumeDbContext, Application>, IApplicationRepository
{
    public ApplicationRepository(ResumeDbContext context) : base(context) { }

    public async Task<bool> ExistsAsync(Guid customerId, Guid jobId)
        => await _dbSet.AnyAsync(a => a.CustomerId == customerId
                                   && a.JobId == jobId
                                   && !a.IsDeleted);

    // Bỏ qua query filter của Resume để load được cả các CV đã bị soft delete
    public new async Task<Application?> GetEntityWithSpec(ISpecification<Application> spec, CancellationToken cancellationToken = default)
    {
        var query = SpecificationEvaluator<Application>.GetQuery(_dbSet.AsNoTracking().IgnoreQueryFilters(), spec);
        return await query.FirstOrDefaultAsync(cancellationToken);
    }

    public new async Task<IReadOnlyList<Application>> ListAsync(ISpecification<Application> spec, CancellationToken cancellationToken = default)
    {
        var query = SpecificationEvaluator<Application>.GetQuery(_dbSet.AsNoTracking().IgnoreQueryFilters(), spec);
        return await query.ToListAsync(cancellationToken);
    }

    public new async Task<int> CountAsync(ISpecification<Application> spec, CancellationToken cancellationToken = default)
    {
        var query = _dbSet.AsNoTracking().IgnoreQueryFilters().AsQueryable();
        if (spec.Criteria != null)
            query = query.Where(spec.Criteria);

        return await query.CountAsync(cancellationToken);
    }
}

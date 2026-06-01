using CommonService.Repository;
using Microsoft.EntityFrameworkCore;
using ResumeService.Data;
using ResumeService.Models;
using ResumeService.Repositories.Interface;

namespace ResumeService.Repositories;

public class ResumeRepository : GenericRepository<ResumeDbContext, Resume>, IResumeRepository
{
    public ResumeRepository(ResumeDbContext context) : base(context) { }

    public async Task<Resume?> GetDefaultByCustomerAsync(Guid customerId)
        => await _dbSet.FirstOrDefaultAsync(r => r.CustomerId == customerId
                                              && r.IsDefault
                                              && !r.IsDeleted);

    public async Task SetDefaultAsync(Guid customerId, Guid resumeId)
    {
        // Bỏ cờ default của tất cả CV cũ
        await _dbSet
            .Where(r => r.CustomerId == customerId && r.IsDefault && !r.IsDeleted)
            .ExecuteUpdateAsync(s => s.SetProperty(r => r.IsDefault, false));

        // Set CV mới làm default
        await _dbSet
            .Where(r => r.Id == resumeId && !r.IsDeleted)
            .ExecuteUpdateAsync(s => s.SetProperty(r => r.IsDefault, true));
    }
}

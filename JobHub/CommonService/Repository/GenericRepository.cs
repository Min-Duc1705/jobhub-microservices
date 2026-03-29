using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace CommonService.Repository
{
    public class GenericRepository<TContext, T> : IGenericRepository<T>
    where TContext : DbContext
    where T : class, ISoftDelete
{
    protected readonly TContext _context;
    protected readonly DbSet<T> _dbSet;

    public GenericRepository(TContext context)
    {
        _context = context;
        _dbSet = context.Set<T>();
    }

    // ---- CRUD cơ bản ----
    public async Task<T?> GetByIdAsync(Guid id)
        => await _dbSet.FindAsync(id);

    // Người dùng thường: chỉ lấy bản ghi chưa bị xóa mềm
    public async Task<IEnumerable<T>> GetAllAsync(CancellationToken cancellationToken = default)
        => await _dbSet.AsNoTracking()
                       .Where(e => !e.IsDeleted)
                       .ToListAsync(cancellationToken);

    // Admin: trả về tất cả, kể cả bản ghi đã Soft Delete
    public async Task<IEnumerable<T>> GetAllIncludingDeletedAsync(CancellationToken cancellationToken = default)
        => await _dbSet.AsNoTracking().ToListAsync(cancellationToken);

    public async Task AddAsync(T entity, CancellationToken cancellationToken = default)
        => await _dbSet.AddAsync(entity, cancellationToken);

    public void Update(T entity)
        => _dbSet.Update(entity);

    // Xóa mềm: chỉ đánh dấu IsDeleted, không DELETE khỏi DB
    public void Delete(T entity)
    {
        entity.IsDeleted = true;
        entity.DeletedAt = DateTimeOffset.UtcNow;
        _dbSet.Update(entity);
    }

    public async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
        => await _context.SaveChangesAsync(cancellationToken);

    // ---- Specification Pattern ----
    public async Task<T?> GetEntityWithSpec(ISpecification<T> spec, CancellationToken cancellationToken = default)
    {
        var query = SpecificationEvaluator<T>.GetQuery(_dbSet.AsNoTracking(), spec);
        return await query.FirstOrDefaultAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<T>> ListAsync(ISpecification<T> spec, CancellationToken cancellationToken = default)
    {
        var query = SpecificationEvaluator<T>.GetQuery(_dbSet.AsNoTracking(), spec);
        return await query.ToListAsync(cancellationToken);
    }

    public async Task<int> CountAsync(ISpecification<T> spec, CancellationToken cancellationToken = default)
    {
        // Count chỉ cần Criteria (WHERE), không cần Paging/OrderBy
        var query = _dbSet.AsNoTracking().AsQueryable();
        if (spec.Criteria != null)
        {
            query = query.Where(spec.Criteria);
        }
        return await query.CountAsync(cancellationToken);
    }
}
}
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace CommonService.Repository
{
    public interface IGenericRepository<T> where T : class
{
    // ---- CRUD cơ bản ----
    Task<T?> GetByIdAsync(Guid id);
    /// <summary>Người dùng thường: chỉ lấy bản ghi chưa bị xóa (IsDeleted = false)</summary>
    Task<IEnumerable<T>> GetAllAsync(CancellationToken cancellationToken = default);

    /// <summary>Admin: lấy tất cả bản ghi kể cả đã Soft Delete</summary>
    Task<IEnumerable<T>> GetAllIncludingDeletedAsync(CancellationToken cancellationToken = default);

    Task AddAsync(T entity, CancellationToken cancellationToken = default);
    void Update(T entity);
    void Delete(T entity);
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);

    // ---- Specification Pattern ----
    /// <summary>Lấy 1 entity duy nhất theo Specification</summary>
    Task<T?> GetEntityWithSpec(ISpecification<T> spec, CancellationToken cancellationToken = default);

    /// <summary>Lấy danh sách entity theo Specification (có filter, sort, paging)</summary>
    Task<IReadOnlyList<T>> ListAsync(ISpecification<T> spec, CancellationToken cancellationToken = default);

    /// <summary>Đếm tổng số bản ghi theo Specification (để tính tổng trang)</summary>
    Task<int> CountAsync(ISpecification<T> spec, CancellationToken cancellationToken = default);
}
}
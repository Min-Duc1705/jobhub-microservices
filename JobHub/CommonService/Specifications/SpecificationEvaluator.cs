using Microsoft.EntityFrameworkCore;

namespace CommonService.Specifications
{
    /// <summary>
    /// Bộ máy biên dịch Specification thành câu truy vấn IQueryable cho EF Core.
    /// GenericRepository sẽ gọi class này để áp dụng toàn bộ điều kiện.
    /// </summary>
    public static class SpecificationEvaluator<T> where T : class
    {
        /// <summary>
        /// Nhận vào IQueryable gốc và 1 Specification,
        /// trả ra IQueryable đã được áp dụng WHERE, Include, OrderBy, Paging.
        /// </summary>
        public static IQueryable<T> GetQuery(IQueryable<T> inputQuery, ISpecification<T> spec)
        {
            var query = inputQuery;

            // 1. Áp dụng WHERE (Criteria)
            if (spec.Criteria != null)
            {
                query = query.Where(spec.Criteria);
            }

            // 2. Áp dụng tất cả Include (lambda style)
            query = spec.Includes.Aggregate(query,
                (current, include) => current.Include(include));

            // 3. Áp dụng Include chuỗi (string style: "Company.Address")
            query = spec.IncludeStrings.Aggregate(query,
                (current, include) => current.Include(include));

            // 4. Áp dụng OrderBy / OrderByDescending
            if (spec.OrderBy != null)
            {
                query = query.OrderBy(spec.OrderBy);
            }
            else if (spec.OrderByDescending != null)
            {
                query = query.OrderByDescending(spec.OrderByDescending);
            }

            // 5. Áp dụng Paging (SKIP + TAKE) nếu được bật
            if (spec.IsPagingEnabled)
            {
                query = query.Skip(spec.Skip).Take(spec.Take);
            }

            return query;
        }
    }
}

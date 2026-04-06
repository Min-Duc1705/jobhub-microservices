using System.Linq.Expressions;

namespace CommonService.Specifications
{
    /// <summary>
    /// Base class cho mọi Specification cụ thể.
    /// Hỗ trợ compose nhiều điều kiện filter riêng từng trường qua AddCriteria(),
    /// thay vì phải viết 1 lambda khổng lồ.
    /// </summary>
    public abstract class BaseSpecification<T> : ISpecification<T>
    {
        // ---- Implement ISpecification ----
        public Expression<Func<T, bool>>?         Criteria           { get; private set; }
        public List<Expression<Func<T, object>>>  Includes           { get; } = new();
        public List<string>                       IncludeStrings     { get; } = new();
        public Expression<Func<T, object>>?       OrderBy            { get; private set; }
        public Expression<Func<T, object>>?       OrderByDescending  { get; private set; }
        public int  Take             { get; private set; }
        public int  Skip             { get; private set; }
        public bool IsPagingEnabled  { get; private set; }

        // ---- Constructor ----

        /// <summary>Specification không có điều kiện WHERE (lấy tất cả)</summary>
        protected BaseSpecification() { }

        /// <summary>Specification có kèm điều kiện WHERE</summary>
        protected BaseSpecification(Expression<Func<T, bool>> criteria)
        {
            Criteria = criteria;
        }

        // ---- Helper methods cho class con dùng ----

        /// <summary>
        /// Thêm 1 điều kiện filter AND vào Criteria hiện tại.
        /// Gọi nhiều lần → tự động AND các điều kiện lại.
        /// Ví dụ:
        ///   AddCriteria(x => !x.IsDeleted);
        ///   AddCriteria(x => x.Module == module);   // nếu module != null
        ///   AddCriteria(x => x.Method == method);   // nếu method != null
        /// </summary>
        protected void AddCriteria(Expression<Func<T, bool>> additionalCriteria)
        {
            if (Criteria == null)
            {
                Criteria = additionalCriteria;
            }
            else
            {
                // Combine: Criteria = Criteria && additionalCriteria
                var param      = Expression.Parameter(typeof(T));
                var leftBody   = Expression.Invoke(Criteria, param);
                var rightBody  = Expression.Invoke(additionalCriteria, param);
                var combined   = Expression.AndAlso(leftBody, rightBody);
                Criteria       = Expression.Lambda<Func<T, bool>>(combined, param);
            }
        }

        /// <summary>Thêm Include kiểu lambda: AddInclude(x => x.Company)</summary>
        protected void AddInclude(Expression<Func<T, object>> includeExpression)
            => Includes.Add(includeExpression);

        /// <summary>Thêm Include kiểu chuỗi: AddInclude("Company.Address")</summary>
        protected void AddInclude(string includeString)
            => IncludeStrings.Add(includeString);

        /// <summary>Sắp xếp tăng dần</summary>
        protected void AddOrderBy(Expression<Func<T, object>> orderByExpression)
            => OrderBy = orderByExpression;

        /// <summary>Sắp xếp giảm dần</summary>
        protected void AddOrderByDescending(Expression<Func<T, object>> orderByDescExpression)
            => OrderByDescending = orderByDescExpression;

        /// <summary>Bật phân trang — pageNumber bắt đầu từ 1</summary>
        protected void ApplyPaging(int skip, int take)
        {
            Skip            = skip;
            Take            = take;
            IsPagingEnabled = true;
        }
    }
}

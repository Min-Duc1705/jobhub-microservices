using System.Linq.Expressions;

namespace CommonService.Specifications
{
    /// <summary>
    /// Base class cho mọi Specification cụ thể.
    /// Các Specification con chỉ cần gọi các method AddInclude(), ApplyOrderBy(), ApplyPaging()
    /// thay vì phải tự implement hết ISpecification.
    /// </summary>
    public abstract class BaseSpecification<T> : ISpecification<T>
    {
        // ---- Implement ISpecification ----
        public Expression<Func<T, bool>>? Criteria { get; private set; }
        public List<Expression<Func<T, object>>> Includes { get; } = new();
        public List<string> IncludeStrings { get; } = new();
        public Expression<Func<T, object>>? OrderBy { get; private set; }
        public Expression<Func<T, object>>? OrderByDescending { get; private set; }
        public int Take { get; private set; }
        public int Skip { get; private set; }
        public bool IsPagingEnabled { get; private set; }

        // ---- Constructor ----

        /// <summary>Specification không có điều kiện WHERE (lấy tất cả)</summary>
        protected BaseSpecification() { }

        /// <summary>Specification có kèm điều kiện WHERE</summary>
        protected BaseSpecification(Expression<Func<T, bool>> criteria)
        {
            Criteria = criteria;
        }

        // ---- Helper methods cho class con dùng ----

        /// <summary>Thêm Include kiểu lambda: AddInclude(x => x.Company)</summary>
        protected void AddInclude(Expression<Func<T, object>> includeExpression)
            => Includes.Add(includeExpression);

        /// <summary>Thêm Include kiểu chuỗi: AddInclude("Company.Address")</summary>
        protected void AddInclude(string includeString)
            => IncludeStrings.Add(includeString);

        /// <summary>Sắp xếp tăng dần</summary>
        protected void ApplyOrderBy(Expression<Func<T, object>> orderByExpression)
            => OrderBy = orderByExpression;

        /// <summary>Sắp xếp giảm dần</summary>
        protected void ApplyOrderByDescending(Expression<Func<T, object>> orderByDescExpression)
            => OrderByDescending = orderByDescExpression;

        /// <summary>Bật phân trang với pageIndex bắt đầu từ 0</summary>
        protected void ApplyPaging(int pageIndex, int pageSize)
        {
            Take = pageSize;
            Skip = pageIndex * pageSize;
            IsPagingEnabled = true;
        }
    }
}

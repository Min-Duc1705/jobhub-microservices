using System.Linq.Expressions;

namespace CommonService.Specifications
{
    /// <summary>
    /// Contract mô tả điều kiện truy vấn: Filter, Sort, Include, Paging.
    /// Mỗi query phức tạp sẽ được đóng gói thành 1 class Specification riêng.
    /// </summary>
    public interface ISpecification<T>
    {
        /// <summary>Điều kiện WHERE (bắt buộc)</summary>
        Expression<Func<T, bool>>? Criteria { get; }

        /// <summary>Danh sách các navigation property cần Include (JOIN)</summary>
        List<Expression<Func<T, object>>> Includes { get; }

        /// <summary>Include dạng chuỗi "ThenInclude" nếu cần (vd: "Company.Address")</summary>
        List<string> IncludeStrings { get; }

        /// <summary>Sắp xếp tăng dần</summary>
        Expression<Func<T, object>>? OrderBy { get; }

        /// <summary>Sắp xếp giảm dần</summary>
        Expression<Func<T, object>>? OrderByDescending { get; }

        /// <summary>Số bản ghi cần lấy (TAKE — dùng cho phân trang)</summary>
        int Take { get; }

        /// <summary>Số bản ghi cần bỏ qua (SKIP — dùng cho phân trang)</summary>
        int Skip { get; }

        /// <summary>Bật/tắt phân trang. True khi Take/Skip đã được gán</summary>
        bool IsPagingEnabled { get; }
    }
}

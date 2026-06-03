using System.Linq.Expressions;
using CommonService.Specifications;
using ProfileService.Models;
using ProfileService.Models.Enums;

namespace ProfileService.Specifications;

/// <summary>Lấy danh sách Customer với filter, sort, phân trang.</summary>
public class CustomerFilterSpec : BaseSpecification<Customer>
{
    public CustomerFilterSpec(
        string?       searchTerm,
        CustomerType? type,
        string?       sortBy,
        bool          isDescending,
        int           pageNumber,
        int           pageSize)
    {
        AddCriteria(c => !c.IsDeleted);
        AddCriteria(c => c.Type != CustomerType.CANDIDATE || c.JobSearchStatus != JobSearchStatus.NOT_LOOKING);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(c =>
                (c.FullName != null && c.FullName.ToLower().Contains(term)) ||
                (c.Phone    != null && c.Phone.ToLower().Contains(term)));
        }

        if (type.HasValue)
            AddCriteria(c => c.Type == type.Value);

        // ── Includes ──────────────────────────────────────────────────────────
        AddInclude(c => c.CustomerSkills);

        // ── Sort ──────────────────────────────────────────────────────────────
        var sortMappings = new Dictionary<string, Expression<Func<Customer, object>>>
        {
            ["fullname"]    = c => c.FullName!,
            ["type"]        = c => c.Type,
            ["createdate"]  = c => c.CreatedDate,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "createdate").ToLower(), c => c.CreatedDate);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        // ── Paging ────────────────────────────────────────────────────────────
        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng Customer phục vụ phân trang — không cần paging/sort.</summary>
public class CustomerFilterCountSpec : BaseSpecification<Customer>
{
    public CustomerFilterCountSpec(string? searchTerm, CustomerType? type)
    {
        AddCriteria(c => !c.IsDeleted);
        AddCriteria(c => c.Type != CustomerType.CANDIDATE || c.JobSearchStatus != JobSearchStatus.NOT_LOOKING);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(c =>
                (c.FullName != null && c.FullName.ToLower().Contains(term)) ||
                (c.Phone    != null && c.Phone.ToLower().Contains(term)));
        }

        if (type.HasValue)
            AddCriteria(c => c.Type == type.Value);
    }
}

/// <summary>Lấy 1 Customer theo Id, kèm Skills.</summary>
public class CustomerByIdSpec : BaseSpecification<Customer>
{
    public CustomerByIdSpec(Guid id)
    {
        AddCriteria(c => c.Id == id);
        AddCriteria(c => !c.IsDeleted);
        AddInclude(c => c.CustomerSkills);
    }
}

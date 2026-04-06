using System.Linq.Expressions;
using AuthService.Models;
using CommonService.Specifications;

namespace AuthService.Specifications;

/// <summary>Lấy danh sách Role với filter theo từng trường, sort, phân trang.</summary>
public class RoleFilterSpec : BaseSpecification<Role>
{
    public RoleFilterSpec(
        string? searchTerm,
        bool?   isActive,
        string? sortBy,
        bool    isDescending,
        int     pageNumber,
        int     pageSize)
    {
        // ── Từng điều kiện filter riêng biệt ──────────────────────────────────
        AddCriteria(r => !r.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(r => r.Name.ToLower().Contains(term) ||
                             (r.Description != null && r.Description.ToLower().Contains(term)));
        }

        if (isActive.HasValue)
            AddCriteria(r => r.Active == isActive.Value);

        // ── Includes ──────────────────────────────────────────────────────────
        AddInclude(r => r.Permissions);

        // ── Sort ──────────────────────────────────────────────────────────────
        var sortMappings = new Dictionary<string, Expression<Func<Role, object>>>
        {
            ["name"]       = r => r.Name,
            ["createdate"] = r => r.CreatedDate,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "name").ToLower(), r => r.Name);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        // ── Paging ────────────────────────────────────────────────────────────
        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng Role phục vụ phân trang — không cần paging/sort.</summary>
public class RoleFilterCountSpec : BaseSpecification<Role>
{
    public RoleFilterCountSpec(string? searchTerm, bool? isActive)
    {
        AddCriteria(r => !r.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(r => r.Name.ToLower().Contains(term) ||
                             (r.Description != null && r.Description.ToLower().Contains(term)));
        }

        if (isActive.HasValue)
            AddCriteria(r => r.Active == isActive.Value);
    }
}

public class RoleByIdSpec : BaseSpecification<Role>
{
    public RoleByIdSpec(Guid id)
    {
        AddCriteria(r => r.Id == id);
        AddCriteria(r => !r.IsDeleted);
        AddInclude(r => r.Permissions);
        AddInclude(r => r.Users);
    }
}

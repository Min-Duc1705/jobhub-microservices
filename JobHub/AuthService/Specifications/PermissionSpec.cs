using System.Linq.Expressions;
using AuthService.Models;
using CommonService.Specifications;

namespace AuthService.Specifications;

/// <summary>Lấy danh sách Permission với filter theo từng trường, sort, phân trang.</summary>
public class PermissionFilterSpec : BaseSpecification<Permission>
{
    public PermissionFilterSpec(
        string? searchTerm,
        string? module,
        string? method,
        string? sortBy,
        bool    isDescending,
        int     pageNumber,
        int     pageSize)
    {
        // ── Từng điều kiện filter riêng biệt ──────────────────────────────────
        AddCriteria(p => !p.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(p => p.Name.ToLower().Contains(term) ||
                             p.ApiPath.ToLower().Contains(term));
        }

        if (!string.IsNullOrWhiteSpace(module))
            AddCriteria(p => p.Module.ToLower() == module.ToLower());

        if (!string.IsNullOrWhiteSpace(method))
            AddCriteria(p => p.Method.ToUpper() == method.ToUpper());

        // ── Sort ──────────────────────────────────────────────────────────────
        var sortMappings = new Dictionary<string, Expression<Func<Permission, object>>>
        {
            ["name"]   = p => p.Name,
            ["module"] = p => p.Module,
            ["method"] = p => p.Method,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "module").ToLower(), p => p.Module);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        // ── Paging ────────────────────────────────────────────────────────────
        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng Permission phục vụ phân trang — không cần paging/sort.</summary>
public class PermissionFilterCountSpec : BaseSpecification<Permission>
{
    public PermissionFilterCountSpec(string? searchTerm, string? module, string? method)
    {
        AddCriteria(p => !p.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(p => p.Name.ToLower().Contains(term) ||
                             p.ApiPath.ToLower().Contains(term));
        }

        if (!string.IsNullOrWhiteSpace(module))
            AddCriteria(p => p.Module.ToLower() == module.ToLower());

        if (!string.IsNullOrWhiteSpace(method))
            AddCriteria(p => p.Method.ToUpper() == method.ToUpper());
    }
}

public class PermissionByIdSpec : BaseSpecification<Permission>
{
    public PermissionByIdSpec(Guid id)
    {
        AddCriteria(p => p.Id == id);
        AddCriteria(p => !p.IsDeleted);
    }
}

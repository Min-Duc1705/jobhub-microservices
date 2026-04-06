using System.Linq.Expressions;
using AuthService.Models;
using CommonService.Specifications;

namespace AuthService.Specifications;

/// <summary>Lấy danh sách User với filter theo từng trường, sort, phân trang.</summary>
public class UserFilterSpec : BaseSpecification<AppUser>
{
    public UserFilterSpec(
        string? searchTerm,
        string? status,
        Guid?   roleId,
        string? sortBy,
        bool    isDescending,
        int     pageNumber,
        int     pageSize)
    {
        // ── Từng điều kiện filter riêng biệt ──────────────────────────────────
        AddCriteria(u => !u.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(u => u.Email.ToLower().Contains(term));
        }

        if (!string.IsNullOrWhiteSpace(status) &&
            Enum.TryParse<UserStatus>(status, true, out var parsedStatus))
            AddCriteria(u => u.Status == parsedStatus);

        if (roleId.HasValue)
            AddCriteria(u => u.RoleId == roleId.Value);

        // ── Includes ──────────────────────────────────────────────────────────
        AddInclude(u => u.Role!);

        // ── Sort ──────────────────────────────────────────────────────────────
        var sortMappings = new Dictionary<string, Expression<Func<AppUser, object>>>
        {
            ["email"]      = u => u.Email,
            ["status"]     = u => u.Status,
            ["createdate"] = u => u.CreatedDate,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "createdate").ToLower(), u => u.CreatedDate);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        // ── Paging ────────────────────────────────────────────────────────────
        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng User phục vụ phân trang — không cần paging/sort.</summary>
public class UserFilterCountSpec : BaseSpecification<AppUser>
{
    public UserFilterCountSpec(string? searchTerm, string? status, Guid? roleId)
    {
        AddCriteria(u => !u.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(u => u.Email.ToLower().Contains(term));
        }

        if (!string.IsNullOrWhiteSpace(status) &&
            Enum.TryParse<UserStatus>(status, true, out var parsedStatus))
            AddCriteria(u => u.Status == parsedStatus);

        if (roleId.HasValue)
            AddCriteria(u => u.RoleId == roleId.Value);
    }
}

public class UserByIdSpec : BaseSpecification<AppUser>
{
    public UserByIdSpec(Guid id)
    {
        AddCriteria(u => u.Id == id);
        AddCriteria(u => !u.IsDeleted);
        AddInclude(u => u.Role!);
    }
}

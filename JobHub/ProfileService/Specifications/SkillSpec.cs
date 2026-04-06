using System.Linq.Expressions;
using CommonService.Specifications;
using ProfileService.Models;

namespace ProfileService.Specifications;

/// <summary>Lấy danh sách Skill với filter, sort, phân trang.</summary>
public class SkillFilterSpec : BaseSpecification<Skill>
{
    public SkillFilterSpec(
        string? searchTerm,
        string? sortBy,
        bool    isDescending,
        int     pageNumber,
        int     pageSize)
    {
        AddCriteria(s => !s.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(s => s.Name.ToLower().Contains(term));
        }

        var sortMappings = new Dictionary<string, Expression<Func<Skill, object>>>
        {
            ["name"]       = s => s.Name,
            ["createdate"] = s => s.CreatedDate,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "name").ToLower(), s => s.Name);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng Skill phục vụ phân trang.</summary>
public class SkillFilterCountSpec : BaseSpecification<Skill>
{
    public SkillFilterCountSpec(string? searchTerm)
    {
        AddCriteria(s => !s.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(s => s.Name.ToLower().Contains(term));
        }
    }
}

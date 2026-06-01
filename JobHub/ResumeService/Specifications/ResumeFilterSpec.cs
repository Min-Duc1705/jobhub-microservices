using System.Linq.Expressions;
using CommonService.Specifications;
using ResumeService.Models;

namespace ResumeService.Specifications;

/// <summary>Lấy danh sách Resume với filter, sort, và phân trang.</summary>
public class ResumeFilterSpec : BaseSpecification<Resume>
{
    public ResumeFilterSpec(
        string? searchTerm,
        Guid?   customerId,
        bool?   isDefault,
        string? sortBy,
        bool    isDescending,
        int     pageNumber,
        int     pageSize)
    {
        AddCriteria(r => !r.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(r => r.Title.ToLower().Contains(term));
        }

        if (customerId.HasValue)
            AddCriteria(r => r.CustomerId == customerId.Value);

        if (isDefault.HasValue)
            AddCriteria(r => r.IsDefault == isDefault.Value);

        var sortMappings = new Dictionary<string, Expression<Func<Resume, object>>>
        {
            ["title"]       = r => r.Title,
            ["createddate"] = r => r.CreatedDate,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "createddate").ToLower(), r => r.CreatedDate);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

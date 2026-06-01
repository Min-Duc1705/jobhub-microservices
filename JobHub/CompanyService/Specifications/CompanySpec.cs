using System.Linq.Expressions;
using CommonService.Specifications;
using CompanyService.Models;
using CompanyService.Models.Enums;

namespace CompanyService.Specifications;

/// <summary>Lấy danh sách Company với filter, sort, phân trang.</summary>
public class CompanyFilterSpec : BaseSpecification<Company>
{
    public CompanyFilterSpec(
        string?      searchTerm,
        string?      industry,
        CompanySize? companySize,
        bool?        isVerified,
        string?      sortBy,
        bool         isDescending,
        int          pageNumber,
        int          pageSize)
    {
        AddCriteria(c => !c.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(c => c.Name.ToLower().Contains(term)
                          || (c.Industry != null && c.Industry.ToLower().Contains(term)));
        }

        if (!string.IsNullOrWhiteSpace(industry))
        {
            var ind = industry.ToLower();
            AddCriteria(c => c.Industry != null && c.Industry.ToLower().Contains(ind));
        }

        if (companySize.HasValue)
            AddCriteria(c => c.CompanySize == companySize.Value);

        if (isVerified.HasValue)
            AddCriteria(c => c.IsVerified == isVerified.Value);

        var sortMappings = new Dictionary<string, Expression<Func<Company, object>>>
        {
            ["name"]        = c => c.Name,
            ["industry"]    = c => c.Industry!,
            ["createddate"] = c => c.CreatedDate,
            ["isverified"]  = c => c.IsVerified,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "createddate").ToLower(), c => c.CreatedDate);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng Company phục vụ phân trang.</summary>
public class CompanyFilterCountSpec : BaseSpecification<Company>
{
    public CompanyFilterCountSpec(
        string?      searchTerm,
        string?      industry,
        CompanySize? companySize,
        bool?        isVerified)
    {
        AddCriteria(c => !c.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(c => c.Name.ToLower().Contains(term)
                          || (c.Industry != null && c.Industry.ToLower().Contains(term)));
        }

        if (!string.IsNullOrWhiteSpace(industry))
        {
            var ind = industry.ToLower();
            AddCriteria(c => c.Industry != null && c.Industry.ToLower().Contains(ind));
        }

        if (companySize.HasValue)
            AddCriteria(c => c.CompanySize == companySize.Value);

        if (isVerified.HasValue)
            AddCriteria(c => c.IsVerified == isVerified.Value);
    }
}

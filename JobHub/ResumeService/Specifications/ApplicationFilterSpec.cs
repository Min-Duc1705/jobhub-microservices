using System.Linq.Expressions;
using CommonService.Specifications;
using ResumeService.Models;
using ResumeService.Models.Enums;

namespace ResumeService.Specifications;

/// <summary>Lấy danh sách Application với filter, sort, và phân trang.</summary>
public class ApplicationFilterSpec : BaseSpecification<Application>
{
    public ApplicationFilterSpec(
        Guid?              customerId,
        Guid?              jobId,
        ApplicationStatus? status,
        string?            sortBy,
        bool               isDescending,
        int                pageNumber,
        int                pageSize)
    {
        AddCriteria(a => !a.IsDeleted);

        if (customerId.HasValue)
            AddCriteria(a => a.CustomerId == customerId.Value);

        if (jobId.HasValue)
            AddCriteria(a => a.JobId == jobId.Value);

        if (status.HasValue)
            AddCriteria(a => a.Status == status.Value);

        // Include Resume để trả về thông tin CV đi kèm
        AddInclude(a => a.Resume);

        var sortMappings = new Dictionary<string, Expression<Func<Application, object>>>
        {
            ["createddate"] = a => a.CreatedDate,
            ["status"]      = a => a.Status,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "createddate").ToLower(), a => a.CreatedDate);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

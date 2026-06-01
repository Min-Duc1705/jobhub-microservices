using CommonService.Specifications;
using ResumeService.Models;
using ResumeService.Models.Enums;

namespace ResumeService.Specifications;

/// <summary>Đếm tổng số Application theo filter (không phân trang).</summary>
public class ApplicationFilterCountSpec : BaseSpecification<Application>
{
    public ApplicationFilterCountSpec(
        Guid?              customerId,
        Guid?              jobId,
        ApplicationStatus? status)
    {
        AddCriteria(a => !a.IsDeleted);

        if (customerId.HasValue)
            AddCriteria(a => a.CustomerId == customerId.Value);

        if (jobId.HasValue)
            AddCriteria(a => a.JobId == jobId.Value);

        if (status.HasValue)
            AddCriteria(a => a.Status == status.Value);
    }
}

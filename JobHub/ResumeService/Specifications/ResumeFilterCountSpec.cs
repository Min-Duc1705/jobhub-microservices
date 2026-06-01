using CommonService.Specifications;
using ResumeService.Models;

namespace ResumeService.Specifications;

/// <summary>Đếm tổng số Resume theo filter (không phân trang).</summary>
public class ResumeFilterCountSpec : BaseSpecification<Resume>
{
    public ResumeFilterCountSpec(string? searchTerm, Guid? customerId, bool? isDefault)
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
    }
}

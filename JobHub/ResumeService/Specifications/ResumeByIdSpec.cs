using CommonService.Specifications;
using ResumeService.Models;

namespace ResumeService.Specifications;

/// <summary>Lấy Resume theo ID.</summary>
public class ResumeByIdSpec : BaseSpecification<Resume>
{
    public ResumeByIdSpec(Guid id)
    {
        AddCriteria(r => r.Id == id && !r.IsDeleted);
    }
}

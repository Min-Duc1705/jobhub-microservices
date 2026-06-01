using CommonService.Specifications;
using ResumeService.Models;

namespace ResumeService.Specifications;

/// <summary>Lấy Application theo ID, bao gồm thông tin Resume.</summary>
public class ApplicationByIdSpec : BaseSpecification<Application>
{
    public ApplicationByIdSpec(Guid id)
    {
        AddCriteria(a => a.Id == id && !a.IsDeleted);
        AddInclude(a => a.Resume);
    }
}

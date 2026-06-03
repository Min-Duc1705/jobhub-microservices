using ProfileService.Models.Enums;

namespace ProfileService.Models.Request;

public class UpdateCustomerRequest
{
    public string? FullName { get; set; }
    public string? Avatar { get; set; }
    public string? Phone { get; set; }
    
    // --- Candidate
    public DateTime? DateOfBirth { get; set; }
    public Gender? Gender { get; set; }
    public string? Address { get; set; }  // VD: "Phường Bến Nghé, Quận 1, Hồ Chí Minh"
    public string? Summary { get; set; }
    public int? YearsOfExperience { get; set; }
    public double? ExpectedSalary { get; set; }
    public JobSearchStatus? JobSearchStatus { get; set; }
    
    // --- Employer
    public Guid? CompanyId { get; set; }
    public string? Position { get; set; }
}

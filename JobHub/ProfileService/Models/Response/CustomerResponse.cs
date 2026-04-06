using ProfileService.Models.Enums;

namespace ProfileService.Models.Response;

public class CustomerResponse
{
    public Guid Id { get; set; }
    public Guid AppUserId { get; set; }
    public CustomerType Type { get; set; }
    
    public string? FullName { get; set; }
    public string? Avatar { get; set; }
    public string? Phone { get; set; }
    
    // Candidate
    public DateTime? DateOfBirth { get; set; }
    public Gender? Gender { get; set; }
    public string? Address { get; set; }
    public string? Summary { get; set; }
    public int? YearsOfExperience { get; set; }
    public double? ExpectedSalary { get; set; }
    public JobSearchStatus? JobSearchStatus { get; set; }
    
    // Employer
    public Guid? CompanyId { get; set; }
    public string? Position { get; set; }
    
    // Skills (Có thể gộp thành string hoặc list nhỏ)
    public List<CustomerSkillDto> Skills { get; set; } = new();
}

public class CustomerSkillDto
{
    public Guid SkillId { get; set; }
    public string SkillName { get; set; } = string.Empty;
    public int? YearsOfExperience { get; set; }
}

using CommonService.Models;
using ProfileService.Models.Enums;

namespace ProfileService.Models;

public class Customer : EntityAuditableBase<Guid>
{
    public Guid AppUserId { get; set; }
    
    public CustomerType Type { get; set; }
    
    // --- Chung
    public string? FullName { get; set; }
    public string? Avatar { get; set; }
    public string? Phone { get; set; }
    
    // --- Đặc thù Candidate
    public DateTime? DateOfBirth { get; set; }
    public Gender? Gender { get; set; }
    public string? Address { get; set; }  // VD: "Phường Bến Nghé, Quận 1, Hồ Chí Minh"
    public string? Summary { get; set; } // Giới thiệu bản thân
    public int? YearsOfExperience { get; set; }
    public double? ExpectedSalary { get; set; }
    public JobSearchStatus? JobSearchStatus { get; set; }
    
    // --- Đặc thù Employer
    public Guid? CompanyId { get; set; }
    public string? Position { get; set; }
    
    // Navigation property
    public virtual ICollection<CustomerSkill> CustomerSkills { get; set; } = new List<CustomerSkill>();
}

using System.ComponentModel.DataAnnotations;

namespace JobService.Models.Request;

public class ImportJobDto
{
    [Required(ErrorMessage = "Tên tin tuyển dụng không được để trống.")]
    public string Name { get; set; } = string.Empty;

    [Required(ErrorMessage = "Tên công ty không được để trống.")]
    public string CompanyName { get; set; } = string.Empty;

    [Required(ErrorMessage = "Email nhà tuyển dụng (HR) không được để trống.")]
    [EmailAddress(ErrorMessage = "Email không đúng định dạng.")]
    public string HREmail { get; set; } = string.Empty;

    public string? Location { get; set; }

    public double? SalaryMin { get; set; }

    public double? SalaryMax { get; set; }

    public string SalaryCurrency { get; set; } = "VND";

    public bool IsSalaryNegotiable { get; set; } = false;

    public int Quantity { get; set; } = 1;

    [Required(ErrorMessage = "Cấp độ (INTERN, FRESHER, JUNIOR, MIDDLE, SENIOR, LEADER, MANAGER) không được để trống.")]
    public string Level { get; set; } = "JUNIOR";

    [Required(ErrorMessage = "Hình thức (FULL_TIME, PART_TIME, REMOTE, HYBRID, INTERNSHIP) không được để trống.")]
    public string JobType { get; set; } = "FULL_TIME";

    public string? ExperienceRequired { get; set; }

    public string? Description { get; set; }

    public string? Requirements { get; set; }

    public string? Benefits { get; set; }

    public string? Category { get; set; }

    public string? Skills { get; set; } // Dạng chuỗi cách nhau bởi dấu phẩy, vd: "C#, React"
}

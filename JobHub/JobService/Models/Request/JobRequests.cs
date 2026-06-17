using JobService.Models.Enums;

namespace JobService.Models.Request;

/// <summary>Tạo tin tuyển dụng mới.</summary>
public class CreateJobRequest
{
    public Guid   CompanyId          { get; set; }
    public string? CompanyName        { get; set; }   // Denormalized — tên công ty
    public string? CompanyLogo        { get; set; }   // Denormalized — URL logo công ty
    public string Name               { get; set; } = string.Empty;
    public string? Location          { get; set; }
    public double? SalaryMin         { get; set; }
    public double? SalaryMax         { get; set; }
    public string  SalaryCurrency    { get; set; } = "VND";
    public bool    IsSalaryNegotiable { get; set; } = false;
    public int     Quantity          { get; set; } = 1;
    public JobLevel  Level           { get; set; } = JobLevel.JUNIOR;
    public JobType   JobType         { get; set; } = JobType.FULL_TIME;
    public string? ExperienceRequired { get; set; }
    public string? Description       { get; set; }
    public string? Requirements      { get; set; }   // Yêu cầu ứng viên (free text)
    public string? Benefits          { get; set; }
    public DateTime? StartDate       { get; set; }
    public DateTime? EndDate         { get; set; }
    public string? Category          { get; set; }

    /// <summary>Danh sách SkillId yêu cầu cho vị trí này.</summary>
    public List<Guid> SkillIds { get; set; } = new();
}

/// <summary>Cập nhật tin tuyển dụng (patch — chỉ map field != null).</summary>
public class UpdateJobRequest
{
    public string? Name               { get; set; }
    public string? CompanyName        { get; set; }   // Denormalized — tên công ty
    public string? CompanyLogo        { get; set; }   // Denormalized — URL logo công ty
    public string? Location           { get; set; }
    public double? SalaryMin          { get; set; }
    public double? SalaryMax          { get; set; }
    public string? SalaryCurrency     { get; set; }
    public bool?   IsSalaryNegotiable { get; set; }
    public int?    Quantity           { get; set; }
    public JobLevel?  Level           { get; set; }
    public JobType?   JobType         { get; set; }
    public string? ExperienceRequired { get; set; }
    public string? Description        { get; set; }
    public string? Requirements       { get; set; }   // Yêu cầu ứng viên (free text)
    public string? Benefits           { get; set; }
    public DateTime? StartDate        { get; set; }
    public DateTime? EndDate          { get; set; }
    public string? Category           { get; set; }
    public JobStatus? Status          { get; set; }
    public List<Guid>? SkillIds       { get; set; }
}

/// <summary>Bộ lọc tìm kiếm Job với phân trang.</summary>
public class JobFilterRequest
{
    public string?   SearchTerm  { get; set; }       // Tìm theo tên job, mô tả
    public Guid?     CompanyId   { get; set; }        // Lọc theo công ty
    public Guid?     CustomerId  { get; set; }        // Lọc theo HR đăng tin
    public string?   Location    { get; set; }        // Lọc theo địa điểm
    public List<JobLevel>? Level { get; set; }
    public List<JobType>?  JobType { get; set; }
    public JobStatus? Status     { get; set; }
    public double?   SalaryMin   { get; set; }        // Lương tối thiểu tìm kiếm
    public double?   SalaryMax   { get; set; }
    public List<Guid>? SkillIds  { get; set; }        // Lọc theo kỹ năng
    public string    SortBy      { get; set; } = "createdDate";
    public bool      IsDescending { get; set; } = true;
    public int       PageNumber  { get; set; } = 1;
    public int       PageSize    { get; set; } = 10;
}

/// <summary>Bộ lọc tìm kiếm Job dành cho Admin — không ép filter Status = PUBLISHED.</summary>
public class AdminJobFilterRequest
{
    public string?    SearchTerm  { get; set; }   // Tìm theo tên job, mô tả, địa điểm
    public Guid?      CompanyId   { get; set; }   // Lọc theo công ty
    public Guid?      CustomerId  { get; set; }   // Lọc theo HR đăng tin (tuỳ chọn)
    public string?    Location    { get; set; }   // Lọc theo địa điểm
    public List<JobLevel>? Level  { get; set; }
    public List<JobType>?  JobType { get; set; }
    public JobStatus? Status      { get; set; }   // Không set = lấy tất cả status
    public string     SortBy      { get; set; } = "createdDate";
    public bool       IsDescending { get; set; } = true;
    public int        PageNumber  { get; set; } = 1;
    public int        PageSize    { get; set; } = 10;
}

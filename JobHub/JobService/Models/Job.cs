using CommonService.Models;
using JobService.Models.Enums;

namespace JobService.Models;

/// <summary>
/// Tin tuyển dụng — entity trung tâm của JobService.
/// CompanyId và CustomerId (HR) không có nav-prop sang service khác (Microservices boundary).
/// </summary>
public class Job : EntityAuditableBase<Guid>
{
    /// <summary>HR (Customer.Type == EMPLOYER) đã đăng bài.</summary>
    public Guid CustomerId { get; set; }

    /// <summary>Công ty đăng tin (reference ID, không FK cross-service).</summary>
    public Guid CompanyId { get; set; }

    public string  Name               { get; set; } = string.Empty;
    public string? CompanyName        { get; set; }   // Denormalized — sync từ CompanyService
    public string? CompanyLogo        { get; set; }   // Denormalized — URL logo công ty
    public string? Location           { get; set; }
    public double? SalaryMin          { get; set; }
    public double? SalaryMax          { get; set; }
    public string  SalaryCurrency     { get; set; } = "VND";
    public bool    IsSalaryNegotiable { get; set; } = false;
    public int     Quantity           { get; set; } = 1;
    public JobLevel  Level            { get; set; } = JobLevel.JUNIOR;
    public JobType   JobType          { get; set; } = JobType.FULL_TIME;
    public string? ExperienceRequired { get; set; }
    public string? Description        { get; set; }
    public string? Requirements       { get; set; }   // Yêu cầu ứng viên (free text)
    public string? Benefits           { get; set; }   // Lưu JSON string hoặc text
    public DateTime? StartDate        { get; set; }
    public DateTime? EndDate          { get; set; }
    public long    ViewCount          { get; set; } = 0;
    public JobStatus Status           { get; set; } = JobStatus.DRAFT;
    public string? Category           { get; set; }

    // ── Navigation ───────────────────────────────────────────────────────────
    public ICollection<JobSkill> JobSkills { get; set; } = new List<JobSkill>();
    public ICollection<SavedJob> SavedJobs { get; set; } = new List<SavedJob>();
}

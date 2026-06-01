using JobService.Models.Enums;

namespace JobService.Models.Response;

public class SkillDto
{
    public Guid   Id   { get; set; }
    public string Name { get; set; } = string.Empty;
}

public class JobResponse
{
    public Guid   Id                  { get; set; }
    public Guid   CompanyId           { get; set; }
    public Guid   CustomerId          { get; set; }
    public string Name                { get; set; } = string.Empty;
    public string? CompanyName        { get; set; }
    public string? CompanyLogo        { get; set; }
    public string? Location           { get; set; }
    public double? SalaryMin          { get; set; }
    public double? SalaryMax          { get; set; }
    public string  SalaryCurrency     { get; set; } = "VND";
    public bool    IsSalaryNegotiable { get; set; }
    public int     Quantity           { get; set; }
    public JobLevel  Level            { get; set; }
    public JobType   JobType          { get; set; }
    public string? ExperienceRequired { get; set; }
    public string? Description        { get; set; }
    public string? Requirements       { get; set; }
    public string? Benefits           { get; set; }
    public DateTime? StartDate        { get; set; }
    public DateTime? EndDate          { get; set; }
    public long    ViewCount          { get; set; }
    public JobStatus Status           { get; set; }
    public string? Category           { get; set; }
    public List<SkillDto> Skills      { get; set; } = new();
    public DateTimeOffset CreatedDate { get; set; }
    public DateTimeOffset? LastModifiedDate { get; set; }
}

public class SkillResponse
{
    public Guid   Id            { get; set; }
    public string Name          { get; set; } = string.Empty;
    public DateTimeOffset CreatedDate { get; set; }
}

public class SavedJobResponse
{
    public Guid   JobId         { get; set; }
    public Guid   CustomerId    { get; set; }
    public DateTimeOffset SavedAt { get; set; }
    public string? Note         { get; set; }
    public JobResponse? Job     { get; set; }
}

public class JobCategoryStatResponse
{
    public string Name { get; set; } = string.Empty;
    public int Count { get; set; }
    public double Percentage { get; set; }
}

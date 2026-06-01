using ResumeService.Models.Enums;

namespace ResumeService.Models.Response;

public class ApplicationResponse
{
    public Guid   Id                   { get; set; }
    public Guid   CustomerId           { get; set; }
    public Guid   JobId                { get; set; }
    public Guid   ResumeId             { get; set; }
    public string? CoverLetter         { get; set; }
    public ApplicationStatus Status    { get; set; }
    public string? ReviewNote          { get; set; }
    public DateTimeOffset  CreatedDate      { get; set; }
    public DateTimeOffset? LastModifiedDate { get; set; }

    /// <summary>Thông tin CV đi kèm (nested DTO).</summary>
    public ResumeResponse? Resume { get; set; }
}

using System;

namespace ResumeService.Models.Response;

public class InterviewResponse
{
    public Guid Id { get; set; }
    public Guid JobId { get; set; }
    public Guid CandidateId { get; set; }
    public Guid RecruiterId { get; set; }
    public DateTimeOffset InterviewDate { get; set; }
    public string Type { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? MeetingLink { get; set; }
    public string? Location { get; set; }
    public string? Notes { get; set; }
    public DateTimeOffset CreatedDate { get; set; }
    public DateTimeOffset? LastModifiedDate { get; set; }
}

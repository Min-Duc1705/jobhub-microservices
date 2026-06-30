using System;

namespace ResumeService.Models.Request;

public class CreateInterviewRequest
{
    public Guid JobId { get; set; }
    public Guid CandidateId { get; set; }
    public DateTimeOffset InterviewDate { get; set; }
    public string Type { get; set; } = "Technical";
    public string? MeetingLink { get; set; }
    public string? Location { get; set; }
    public string? Notes { get; set; }
}

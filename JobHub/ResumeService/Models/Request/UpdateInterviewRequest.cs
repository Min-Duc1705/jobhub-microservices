using System;

namespace ResumeService.Models.Request;

public class UpdateInterviewRequest
{
    public DateTimeOffset InterviewDate { get; set; }
    public string? Status { get; set; }
    public string? MeetingLink { get; set; }
    public string? Location { get; set; }
    public string? Notes { get; set; }
}

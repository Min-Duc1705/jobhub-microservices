using System;

namespace CommonService.Events;

public class InterviewScheduleChangedEvent
{
    public Guid InterviewId { get; set; }
    public string RecruiterId { get; set; } = string.Empty;
    public string CandidateId { get; set; } = string.Empty;
    public string JobId { get; set; } = string.Empty;
    public DateTimeOffset InterviewDate { get; set; }
    public string Type { get; set; } = string.Empty; // Technical, Cultural, Final
    public string Status { get; set; } = string.Empty; // PendingConfirm, Scheduled, Rescheduled, Cancelled, Completed
    public string? MeetingLink { get; set; }
    public string? Notes { get; set; }
    public string Action { get; set; } = string.Empty; // Create, Update, Delete
}

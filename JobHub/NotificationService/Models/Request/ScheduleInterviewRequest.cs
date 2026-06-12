using System;

namespace NotificationService.Models.Request;

public class ScheduleInterviewRequest
{
    /// <summary>ID của ứng viên (HR cung cấp khi đặt lịch)</summary>
    public string CandidateId { get; set; } = string.Empty;
    public DateTimeOffset InterviewDate { get; set; }
}

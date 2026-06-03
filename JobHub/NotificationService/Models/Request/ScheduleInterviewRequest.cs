using System;

namespace NotificationService.Models.Request;

public class ScheduleInterviewRequest
{
    public DateTimeOffset InterviewDate { get; set; }
}

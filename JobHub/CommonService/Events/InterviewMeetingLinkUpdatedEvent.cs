using System;

namespace CommonService.Events;

public class InterviewMeetingLinkUpdatedEvent
{
    public Guid InterviewId { get; set; }
    public string MeetingLink { get; set; } = string.Empty;
}

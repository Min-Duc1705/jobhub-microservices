using System;

namespace CommonService.Events;

/// <summary>
/// Phát sinh khi User bị xóa khỏi hệ thống.
/// -> Các service khác lắng nghe để xóa thông tin liên quan (Customer, Resumes, Applications, Jobs, SavedJobs).
/// </summary>
public class UserDeletedEvent
{
    public Guid UserId { get; set; }
}

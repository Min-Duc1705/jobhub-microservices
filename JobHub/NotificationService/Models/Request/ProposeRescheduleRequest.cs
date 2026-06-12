namespace NotificationService.Models.Request;

public class ProposeRescheduleRequest
{
    /// <summary>Lý do hoặc ghi chú của ứng viên khi đề xuất đổi lịch (tùy chọn)</summary>
    public string? Message { get; set; }
}

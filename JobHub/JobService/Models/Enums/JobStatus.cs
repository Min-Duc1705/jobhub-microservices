namespace JobService.Models.Enums;

public enum JobStatus
{
    DRAFT,      // Bản nháp chưa đăng
    PUBLISHED,  // Đang tuyển (public)
    CLOSED,     // Hết hạn hoặc tuyển đủ
    SUSPENDED   // Admin khoá
}

using CommonService.Models;

namespace AuthService.Models
{
    /// <summary>
    /// Tài khoản định danh — chỉ chứa thông tin bảo mật cho việc đăng nhập.
    /// KHÔNG chứa thông tin cá nhân (tên, tuổi...), phần đó thuộc ProfileService.
    /// </summary>
    public class AppUser : EntityAuditableBase<Guid>
    {
        /// <summary>Email dùng làm username đăng nhập. Unique Index.</summary>
        public string Email { get; set; } = string.Empty;

        /// <summary>Tên hiển thị / username do người dùng chọn.</summary>
        public string Username { get; set; } = string.Empty;

        /// <summary>Mật khẩu đã được băm (BCrypt). KHÔNG BAO GIỜ lưu plain text.</summary>
        public string PasswordHash { get; set; } = string.Empty;

        /// <summary>Trạng thái tài khoản.</summary>
        public UserStatus Status { get; set; } = UserStatus.Pending;

        /// <summary>Refresh Token dùng để cấp lại Access Token mà không cần đăng nhập lại.</summary>
        public string? RefreshToken { get; set; }


        // --- Navigation ---
        public Guid RoleId { get; set; }
        public Role Role { get; set; } = null!;
    }

    public enum UserStatus
    {
        /// <summary>Chờ xác minh Email.</summary>
        Pending,

        /// <summary>Tài khoản đang hoạt động bình thường.</summary>
        Active,

        /// <summary>Bị khoá bởi Admin (vi phạm nội quy).</summary>
        Suspended,

        /// <summary>Người dùng tự vô hiệu hoá tài khoản.</summary>
        Deactivated
    }
}

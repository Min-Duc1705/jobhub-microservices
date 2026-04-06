using CommonService.Models;

namespace AuthService.Models
{
    public class Permission : EntityAuditableBase<Guid>
    {
        /// <summary>Tên mô tả quyền. Ví dụ: "Xem danh sách Job", "Tạo tin tuyển dụng".</summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>Đường dẫn API được bảo vệ. Ví dụ: "/api/v1/jobs", "/api/v1/jobs/{id}".</summary>
        public string ApiPath { get; set; } = string.Empty;

        /// <summary>HTTP Method. Ví dụ: GET, POST, PUT, DELETE.</summary>
        public string Method { get; set; } = string.Empty;

        /// <summary>Module chức năng để nhóm Permission trên UI Admin. Ví dụ: JOB, RESUME, USER.</summary>
        public string Module { get; set; } = string.Empty;

        // --- Navigation (EF tự tạo bảng trung gian RolePermissions) ---
        public ICollection<Role> Roles { get; set; } = new List<Role>();
    }
}

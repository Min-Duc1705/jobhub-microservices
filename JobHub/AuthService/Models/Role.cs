using CommonService.Models;

namespace AuthService.Models
{
    public class Role : EntityAuditableBase<Guid>
    {
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public bool Active { get; set; } = true;

        // --- Navigation ---
        public ICollection<AppUser> Users { get; set; } = new List<AppUser>();
        public ICollection<Permission> Permissions { get; set; } = new List<Permission>();
    }
}

namespace AuthService.Models.Request
{
    public class RoleFilterRequest
    {
        public string? SearchTerm   { get; set; }
        public bool?   IsActive     { get; set; }
        public string? SortBy       { get; set; }
        public bool    IsDescending { get; set; } = false;
        public int     PageNumber   { get; set; } = 1;
        public int     PageSize     { get; set; } = 10;
    }

    public class CreateRoleRequest
    {
        public string       Name          { get; set; } = string.Empty;
        public string?      Description   { get; set; }
        public List<Guid>   PermissionIds { get; set; } = new();
    }

    public class UpdateRoleRequest
    {
        public string       Name          { get; set; } = string.Empty;
        public string?      Description   { get; set; }
        public bool         IsActive      { get; set; } = true;
        public List<Guid>?  PermissionIds { get; set; }
    }
}

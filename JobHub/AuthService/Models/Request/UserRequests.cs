namespace AuthService.Models.Request
{
    public class UserFilterRequest
    {
        public string? SearchTerm   { get; set; }
        public string? Status       { get; set; } // "Active", "Pending", "Suspended", "Deactivated"
        public Guid?   RoleId       { get; set; }
        public string? SortBy       { get; set; }
        public bool    IsDescending { get; set; } = false;
        public int     PageNumber   { get; set; } = 1;
        public int     PageSize     { get; set; } = 10;
    }

    public class CreateUserRequest
    {
        public string  Username { get; set; } = string.Empty;
        public string  Email    { get; set; } = string.Empty;
        public string  Password { get; set; } = string.Empty;
        public Guid?   RoleId   { get; set; }
    }

    public class UpdateUserRequest
    {
        public string  Username { get; set; } = string.Empty;
        public string  Email    { get; set; } = string.Empty;
        public string  Status   { get; set; } = "Active";
        public Guid?   RoleId   { get; set; }
    }
}

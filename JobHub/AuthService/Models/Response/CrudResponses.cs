namespace AuthService.Models.Response
{
    public class UserResponse
    {
        public Guid          Id          { get; set; }
        public string        Username    { get; set; } = string.Empty;
        public string        Email       { get; set; } = string.Empty;
        public string        Status      { get; set; } = string.Empty;
        public DateTimeOffset CreatedDate { get; set; }
        public DateTimeOffset? LastModifiedDate { get; set; }
        public RoleDto?      Role        { get; set; }

        public class RoleDto
        {
            public Guid   Id   { get; set; }
            public string Name { get; set; } = string.Empty;
        }
    }

    public class RoleResponse
    {
        public Guid                    Id          { get; set; }
        public string                  Name        { get; set; } = string.Empty;
        public string?                 Description { get; set; }
        public bool                    IsActive    { get; set; }
        public int                     UserCount   { get; set; }
        public List<PermissionResponse> Permissions { get; set; } = new();
        public DateTimeOffset          CreatedDate { get; set; }
        public DateTimeOffset?         LastModifiedDate { get; set; }
    }

    public class RoleDropdownDto
    {
        public Guid   Id   { get; set; }
        public string Name { get; set; } = string.Empty;
    }

    public class PermissionResponse
    {
        public Guid    Id      { get; set; }
        public string  Name    { get; set; } = string.Empty;
        public string  ApiPath { get; set; } = string.Empty;
        public string  Method  { get; set; } = string.Empty;
        public string  Module  { get; set; } = string.Empty;
        public DateTimeOffset  CreatedDate { get; set; }
        public DateTimeOffset? LastModifiedDate { get; set; }
    }
}

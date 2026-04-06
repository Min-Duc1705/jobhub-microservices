namespace AuthService.Models.Request
{
    public class PermissionFilterRequest
    {
        public string? SearchTerm   { get; set; }
        public string? Module       { get; set; }
        public string? Method       { get; set; }
        public string? SortBy       { get; set; }
        public bool    IsDescending { get; set; } = false;
        public int     PageNumber   { get; set; } = 1;
        public int     PageSize     { get; set; } = 10;
    }

    public class CreatePermissionRequest
    {
        public string Name    { get; set; } = string.Empty;
        public string ApiPath { get; set; } = string.Empty;
        public string Method  { get; set; } = string.Empty;
        public string Module  { get; set; } = string.Empty;
    }

    public class UpdatePermissionRequest
    {
        public string Name    { get; set; } = string.Empty;
        public string ApiPath { get; set; } = string.Empty;
        public string Method  { get; set; } = string.Empty;
        public string Module  { get; set; } = string.Empty;
    }
}

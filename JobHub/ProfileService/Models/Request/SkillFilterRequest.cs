namespace ProfileService.Models.Request;

public class SkillFilterRequest
{
    public string? SearchTerm   { get; set; }
    public string? SortBy       { get; set; }
    public bool    IsDescending { get; set; } = false;
    public int     PageNumber   { get; set; } = 1;
    public int     PageSize     { get; set; } = 10;
}

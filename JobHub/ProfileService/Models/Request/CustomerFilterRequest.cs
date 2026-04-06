using ProfileService.Models.Enums;

namespace ProfileService.Models.Request;

public class CustomerFilterRequest
{
    public string?       SearchTerm   { get; set; } // Tìm theo FullName hoặc Phone
    public CustomerType? Type         { get; set; } // Lọc theo CANDIDATE / EMPLOYER
    public string?       SortBy       { get; set; }
    public bool          IsDescending { get; set; } = false;
    public int           PageNumber   { get; set; } = 1;
    public int           PageSize     { get; set; } = 10;
}

namespace ResumeService.Models.Request;

/// <summary>Tạo CV mới (Ứng viên upload).</summary>
public class CreateResumeRequest
{
    public string Title     { get; set; } = string.Empty;
    public string Url       { get; set; } = string.Empty;
    public string? ExtractedText { get; set; }
    public bool   IsDefault { get; set; } = false;
}

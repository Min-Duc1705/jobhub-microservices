namespace ResumeService.Models.Request;

/// <summary>Cập nhật CV (patch — chỉ map field != null).</summary>
public class UpdateResumeRequest
{
    public string? Title     { get; set; }
    public string? Url       { get; set; }
    public string? ExtractedText { get; set; }
    public bool?   IsDefault { get; set; }
}

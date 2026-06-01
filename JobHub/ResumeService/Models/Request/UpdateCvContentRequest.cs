namespace ResumeService.Models.Request;

/// <summary>
/// Cập nhật nội dung CV Online (auto-save từ builder).
/// </summary>
public class UpdateCvContentRequest
{
    public string? Title       { get; set; }
    public int?    TemplateId  { get; set; }
    public string? ContentJson { get; set; }
    public bool?   IsDefault   { get; set; }
}

namespace ResumeService.Models.Request;

/// <summary>
/// Tạo CV Online bằng Builder (không phải file upload).
/// ContentJson chứa dữ liệu CV dạng JSON (ResumeContent từ frontend).
/// </summary>
public class CreateOnlineCvRequest
{
    public string Title       { get; set; } = "CV của tôi";
    public int    TemplateId  { get; set; } = 1;
    public string ContentJson { get; set; } = "{}";
    public bool   IsDefault   { get; set; } = false;
}

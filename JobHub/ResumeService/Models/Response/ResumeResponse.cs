namespace ResumeService.Models.Response;

public class ResumeResponse
{
    public Guid   Id                   { get; set; }
    public Guid   CustomerId           { get; set; }
    public string Title                { get; set; } = string.Empty;
    public string? Url                 { get; set; }
    public string? ExtractedText       { get; set; }
    public bool   IsDefault            { get; set; }
    public bool   IsOnlineCv           { get; set; }
    public int?   TemplateId           { get; set; }
    public string? ContentJson         { get; set; }
    public DateTimeOffset  CreatedDate      { get; set; }
    public DateTimeOffset? LastModifiedDate { get; set; }
}

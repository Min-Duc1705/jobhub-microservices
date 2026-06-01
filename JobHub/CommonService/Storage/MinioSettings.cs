namespace CommonService.Storage;

public class MinioSettings
{
    public const string SectionName = "MinIO";

    public string Endpoint { get; set; } = string.Empty;
    public string ExternalEndpoint { get; set; } = string.Empty;
    public string AccessKey { get; set; } = string.Empty;
    public string SecretKey { get; set; } = string.Empty;
    public bool Secure { get; set; } = false;
}

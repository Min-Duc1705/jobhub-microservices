namespace CommonService.File;

/// <summary>Kết quả sau khi upload một file lên MinIO.</summary>
public class FileUploadResult
{
    /// <summary>URL công khai truy cập trực tiếp (http://minio-host/bucket/objectName).</summary>
    public string Url        { get; init; } = string.Empty;

    /// <summary>Tên object trong bucket (UUID + extension), dùng để download / delete.</summary>
    public string ObjectName { get; init; } = string.Empty;

    /// <summary>Tên file gốc của người dùng.</summary>
    public string OriginalFileName { get; init; } = string.Empty;
}

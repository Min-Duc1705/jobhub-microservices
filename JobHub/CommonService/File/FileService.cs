using CommonService.Storage;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Options;

namespace CommonService.File;

/// <summary>
/// Implementation của <see cref="IFileService"/> dùng MinIO làm storage backend.
/// URL công khai được build từ <see cref="MinioSettings"/> thay vì hardcode.
/// </summary>
public class FileService : IFileService
{
    private readonly IMinioStorageService _storage;
    private readonly MinioSettings        _settings;

    public FileService(IMinioStorageService storage, IOptions<MinioSettings> settings)
    {
        _storage  = storage;
        _settings = settings.Value;
    }

    // ── Upload single ─────────────────────────────────────────────────────────

    public async Task<FileUploadResult> UploadAsync(
        IFormFile  file,
        string     bucketName,
        string[]?  allowedExtensions = null,
        long       maxSizeBytes      = 0)
    {
        ValidateFile(file, allowedExtensions, maxSizeBytes);

        var extension  = Path.GetExtension(file.FileName).ToLowerInvariant();
        var objectName = $"{Guid.NewGuid()}{extension}";

        using var stream = file.OpenReadStream();
        await _storage.UploadFileAsync(bucketName, objectName, stream, file.ContentType);

        return BuildResult(bucketName, objectName, file.FileName);
    }

    // ── Upload many ───────────────────────────────────────────────────────────

    public async Task<IReadOnlyList<FileUploadResult>> UploadManyAsync(
        IEnumerable<IFormFile> files,
        string                 bucketName,
        string[]?              allowedExtensions = null,
        long                   maxSizeBytes      = 0,
        int                    maxCount          = 10)
    {
        var list = files.ToList();

        if (list.Count > maxCount)
            throw new ArgumentException($"Tối đa {maxCount} file mỗi lần upload. Bạn đã chọn {list.Count} file.");

        var results = new List<FileUploadResult>(list.Count);
        foreach (var file in list)
            results.Add(await UploadAsync(file, bucketName, allowedExtensions, maxSizeBytes));

        return results.AsReadOnly();
    }

    // ── Download ──────────────────────────────────────────────────────────────

    public Task<Stream> DownloadAsync(string bucketName, string objectName)
        => _storage.DownloadFileAsync(bucketName, objectName);

    // ── Delete ────────────────────────────────────────────────────────────────

    public Task DeleteAsync(string bucketName, string objectName)
        => _storage.DeleteFileAsync(bucketName, objectName);

    // ── Presigned URL ─────────────────────────────────────────────────────────

    public Task<string> GetPresignedUrlAsync(string bucketName, string objectName, int expirySeconds = 3600)
        => _storage.GetPresignedUrlAsync(bucketName, objectName, expirySeconds);

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static void ValidateFile(IFormFile file, string[]? allowedExtensions, long maxSizeBytes)
    {
        if (file == null || file.Length == 0)
            throw new ArgumentException("Vui lòng chọn file hợp lệ.");

        if (allowedExtensions is { Length: > 0 })
        {
            var ext = Path.GetExtension(file.FileName).ToLowerInvariant();
            if (!allowedExtensions.Contains(ext))
                throw new ArgumentException(
                    $"Định dạng không hỗ trợ. Chỉ chấp nhận: {string.Join(", ", allowedExtensions)}.");
        }

        if (maxSizeBytes > 0 && file.Length > maxSizeBytes)
            throw new ArgumentException(
                $"File quá lớn. Tối đa {maxSizeBytes / 1024 / 1024} MB.");
    }

    /// <summary>Build URL công khai từ MinioSettings endpoint (không hardcode localhost).</summary>
    private FileUploadResult BuildResult(string bucketName, string objectName, string originalFileName)
    {
        // Build public URL: http(s)://endpoint/bucket/objectName
        var scheme = _settings.Secure ? "https" : "http";
        var url    = $"{scheme}://{_settings.Endpoint}/{bucketName}/{objectName}";

        return new FileUploadResult
        {
            Url              = url,
            ObjectName       = objectName,
            OriginalFileName = originalFileName,
        };
    }
}

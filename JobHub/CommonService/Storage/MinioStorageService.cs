using System.IO;
using Microsoft.Extensions.Options;
using Minio;
using Minio.DataModel.Args;

namespace CommonService.Storage;

public class MinioStorageService : IMinioStorageService
{
    private readonly IMinioClient    _minioClient;
    private readonly MinioSettings   _settings;

    public MinioStorageService(IOptions<MinioSettings> settings)
    {
        _settings = settings.Value;

        var clientBuilder = new MinioClient()
            .WithEndpoint(_settings.Endpoint)
            .WithCredentials(_settings.AccessKey, _settings.SecretKey);

        if (_settings.Secure)
            clientBuilder = clientBuilder.WithSSL();

        _minioClient = clientBuilder.Build();
    }

    // ── Bucket ────────────────────────────────────────────────────────────────

    public async Task<bool> BucketExistsAsync(string bucketName)
    {
        var args = new BucketExistsArgs().WithBucket(bucketName);
        return await _minioClient.BucketExistsAsync(args);
    }

    /// <summary>
    /// Tạo bucket nếu chưa tồn tại.
    /// Bucket access control được quản lý qua presigned URL (không cần public policy).
    /// </summary>
    public async Task CreateBucketAsync(string bucketName)
    {
        if (!await BucketExistsAsync(bucketName))
        {
            await _minioClient.MakeBucketAsync(new MakeBucketArgs().WithBucket(bucketName));
        }
    }

    // ── Objects ───────────────────────────────────────────────────────────────

    public async Task<string> UploadFileAsync(
        string bucketName, string objectName, Stream fileStream, string contentType)
    {
        await CreateBucketAsync(bucketName);

        var args = new PutObjectArgs()
            .WithBucket(bucketName)
            .WithObject(objectName)
            .WithStreamData(fileStream)
            .WithObjectSize(fileStream.Length)
            .WithContentType(contentType);

        await _minioClient.PutObjectAsync(args);
        return objectName;
    }

    public async Task<Stream> DownloadFileAsync(string bucketName, string objectName)
    {
        var memoryStream = new MemoryStream();

        var args = new GetObjectArgs()
            .WithBucket(bucketName)
            .WithObject(objectName)
            .WithCallbackStream(stream => stream.CopyTo(memoryStream));

        await _minioClient.GetObjectAsync(args);
        memoryStream.Position = 0;
        return memoryStream;
    }

    public async Task DeleteFileAsync(string bucketName, string objectName)
    {
        var args = new RemoveObjectArgs()
            .WithBucket(bucketName)
            .WithObject(objectName);

        await _minioClient.RemoveObjectAsync(args);
    }

    public async Task<string> GetPresignedUrlAsync(
        string bucketName, string objectName, int expiryInSeconds = 3600)
    {
        // PresignedGetObjectArgs — đúng API trong Minio SDK 6.x
        var args = new PresignedGetObjectArgs()
            .WithBucket(bucketName)
            .WithObject(objectName)
            .WithExpiry(expiryInSeconds);

        var url = await _minioClient.PresignedGetObjectAsync(args);
        
        // Thay thế endpoint nội bộ bằng endpoint ngoại bộ cho Client truy cập
        if (!string.IsNullOrEmpty(_settings.ExternalEndpoint) && _settings.Endpoint != _settings.ExternalEndpoint)
        {
            url = url.Replace(_settings.Endpoint, _settings.ExternalEndpoint);
            
            // Tự động nâng cấp lên https cho các tên miền public như ngrok hoặc cloudflare để tránh lỗi Mixed Content
            if (_settings.ExternalEndpoint.Contains("ngrok-free.dev") || _settings.ExternalEndpoint.Contains("ngrok-free.app") || _settings.ExternalEndpoint.Contains("trycloudflare.com"))
            {
                url = url.Replace("http://", "https://");
            }
        }
        
        return url;
    }
}

using System.IO;
using System.Threading.Tasks;

namespace CommonService.Storage;

public interface IMinioStorageService
{
    Task<bool> BucketExistsAsync(string bucketName);
    Task CreateBucketAsync(string bucketName);
    Task<string> UploadFileAsync(string bucketName, string objectName, Stream fileStream, string contentType);
    Task<Stream> DownloadFileAsync(string bucketName, string objectName);
    Task DeleteFileAsync(string bucketName, string objectName);
    Task<string> GetPresignedUrlAsync(string bucketName, string objectName, int expiryInSeconds = 3600);
}

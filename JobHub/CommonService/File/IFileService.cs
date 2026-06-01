using Microsoft.AspNetCore.Http;

namespace CommonService.File;

/// <summary>
/// Service tái sử dụng cho việc upload / download / delete file qua MinIO.
/// Inject vào bất kỳ Controller nào cần xử lý file mà không lặp logic validate.
/// </summary>
public interface IFileService
{
    /// <summary>
    /// Upload một file lên MinIO bucket chỉ định.
    /// Tự động validate extension, sinh UUID objectName, tạo bucket nếu chưa có.
    /// </summary>
    /// <param name="file">File từ IFormFile.</param>
    /// <param name="bucketName">Tên bucket đích (VD: "companies", "avatars", "resumes").</param>
    /// <param name="allowedExtensions">
    ///   Danh sách extension được phép, VD: [".jpg",".png"].
    ///   Null/empty = không giới hạn extension.
    /// </param>
    /// <param name="maxSizeBytes">Giới hạn kích thước file (bytes). 0 = không giới hạn.</param>
    /// <returns>Kết quả upload gồm URL công khai và tên object.</returns>
    /// <exception cref="ArgumentException">Extension không hợp lệ hoặc file vượt quá kích thước.</exception>
    Task<FileUploadResult> UploadAsync(
        IFormFile  file,
        string     bucketName,
        string[]?  allowedExtensions = null,
        long       maxSizeBytes      = 0);

    /// <summary>
    /// Upload nhiều file cùng lúc (tối đa <paramref name="maxCount"/> file).
    /// Mỗi file đều được validate riêng lẻ.
    /// </summary>
    Task<IReadOnlyList<FileUploadResult>> UploadManyAsync(
        IEnumerable<IFormFile> files,
        string                 bucketName,
        string[]?              allowedExtensions = null,
        long                   maxSizeBytes      = 0,
        int                    maxCount          = 10);

    /// <summary>Download file từ MinIO, trả về Stream.</summary>
    Task<Stream> DownloadAsync(string bucketName, string objectName);

    /// <summary>Xoá file khỏi MinIO.</summary>
    Task DeleteAsync(string bucketName, string objectName);

    /// <summary>Lấy presigned URL (có thời hạn) thay vì URL công khai.</summary>
    Task<string> GetPresignedUrlAsync(string bucketName, string objectName, int expirySeconds = 3600);
}

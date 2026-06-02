using System;

namespace CommonService.Storage;

public static class MinioUrlHelper
{
    /// <summary>
    /// Chuyển đổi relative path dạng "filename.ext" hoặc "bucket/filename.ext" thành URL tuyệt đối để trả về cho client.
    /// </summary>
    public static string? ToAbsoluteUrl(string? relativePath, MinioSettings? settings, string bucketName)
    {
        if (string.IsNullOrWhiteSpace(relativePath)) return relativePath;

        // Nếu đã là URL tuyệt đối thì giữ nguyên
        if (relativePath.StartsWith("http://", StringComparison.OrdinalIgnoreCase) || 
            relativePath.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
        {
            return relativePath;
        }

        if (settings == null) return relativePath;

        var scheme = settings.Secure ? "https" : "http";
        var endpoint = string.IsNullOrEmpty(settings.ExternalEndpoint) ? settings.Endpoint : settings.ExternalEndpoint;

        // Nâng cấp lên https cho các domain ngrok/cloudflare tránh lỗi Mixed Content
        if (endpoint.Contains("ngrok-free.dev") || 
            endpoint.Contains("ngrok-free.app") || 
            endpoint.Contains("trycloudflare.com"))
        {
            scheme = "https";
        }

        // Đảm bảo relativePath bắt đầu bằng bucketName/
        var cleanPath = relativePath.TrimStart('/');
        if (!cleanPath.StartsWith(bucketName + "/", StringComparison.OrdinalIgnoreCase))
        {
            cleanPath = $"{bucketName}/{cleanPath}";
        }

        return $"{scheme}://{endpoint}/{cleanPath}";
    }

    /// <summary>
    /// Chuyển đổi danh sách relative paths thành danh sách URLs tuyệt đối.
    /// </summary>
    public static System.Collections.Generic.List<string>? ToAbsoluteUrls(System.Collections.Generic.List<string>? relativePaths, MinioSettings? settings, string bucketName)
    {
        if (relativePaths == null) return null;
        var list = new System.Collections.Generic.List<string>(relativePaths.Count);
        foreach (var path in relativePaths)
        {
            var abs = ToAbsoluteUrl(path, settings, bucketName);
            if (abs != null) list.Add(abs);
        }
        return list;
    }

    /// <summary>
    /// Chuẩn hóa URL tuyệt đối hoặc tương đối về dạng đường dẫn tương đối để lưu vào Database.
    /// </summary>
    public static string? ToRelativePath(string? url)
    {
        if (string.IsNullOrWhiteSpace(url)) return url;

        if (!url.StartsWith("http://", StringComparison.OrdinalIgnoreCase) && 
            !url.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
        {
            return url;
        }

        try
        {
            var uri = new Uri(url);
            // Lấy AbsolutePath và xóa dấu '/' ở đầu (ví dụ: "/avatars/abc.png" -> "avatars/abc.png")
            return uri.AbsolutePath.TrimStart('/');
        }
        catch
        {
            return url;
        }
    }

    /// <summary>
    /// Chuẩn hóa danh sách URLs thành danh sách relative paths.
    /// </summary>
    public static System.Collections.Generic.List<string>? ToRelativePaths(System.Collections.Generic.List<string>? urls)
    {
        if (urls == null) return null;
        var list = new System.Collections.Generic.List<string>(urls.Count);
        foreach (var url in urls)
        {
            var rel = ToRelativePath(url);
            if (rel != null) list.Add(rel);
        }
        return list;
    }
}

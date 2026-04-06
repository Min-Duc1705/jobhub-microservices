namespace CommonService.Caching;

public interface ICacheService
{
    /// <summary>Lấy dữ liệu từ Cache theo Key, tự động Deserialize ra kiểu T</summary>
    Task<T?> GetAsync<T>(string key);

    /// <summary>Lưu dữ liệu vào Cache, tự động Serialize Object sang Json</summary>
    Task SetAsync<T>(string key, T data, TimeSpan? absoluteExpireTime = null, TimeSpan? slidingExpireTime = null);

    /// <summary>Xóa Cache theo Key</summary>
    Task RemoveAsync(string key);
}

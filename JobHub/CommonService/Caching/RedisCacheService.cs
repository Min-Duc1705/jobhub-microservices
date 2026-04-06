using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;

namespace CommonService.Caching;

public class RedisCacheService : ICacheService
{
    private readonly IDistributedCache _distributedCache;

    public RedisCacheService(IDistributedCache distributedCache)
    {
        _distributedCache = distributedCache;
    }

    public async Task<T?> GetAsync<T>(string key)
    {
        var cachedData = await _distributedCache.GetStringAsync(key);
        if (string.IsNullOrEmpty(cachedData))
            return default;

        return JsonSerializer.Deserialize<T>(cachedData);
    }

    public async Task SetAsync<T>(string key, T data, TimeSpan? absoluteExpireTime = null, TimeSpan? slidingExpireTime = null)
    {
        var options = new DistributedCacheEntryOptions();

        if (absoluteExpireTime.HasValue)
            options.AbsoluteExpirationRelativeToNow = absoluteExpireTime;
        else if (slidingExpireTime.HasValue)
            options.SlidingExpiration = slidingExpireTime;
        else
            // Default 1 ngày nếu không cung cấp
            options.AbsoluteExpirationRelativeToNow = TimeSpan.FromDays(1);

        var serializedData = JsonSerializer.Serialize(data);
        await _distributedCache.SetStringAsync(key, serializedData, options);
    }

    public async Task RemoveAsync(string key)
        => await _distributedCache.RemoveAsync(key);
}

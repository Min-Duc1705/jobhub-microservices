namespace CommonService.Filters;

/// <summary>
/// Đánh dấu Controller/Action cần kiểm tra Permission từ Redis Cache.
/// 
/// Cách dùng trên Controller (tất cả action):
///   [RequiresPermission("GET", "/api/v1/jobs")]
///   public class JobsController : ControllerBase { ... }
///
/// Cách dùng trên từng Action (granular — ưu tiên hơn class-level):
///   [HttpGet("{id}")]
///   [RequiresPermission("GET", "/api/v1/jobs/{id}")]
///   public async Task&lt;IActionResult&gt; GetById(Guid id) { ... }
///
/// Action/Controller KHÔNG có attribute → RequiresPermissionFilter BỎ QUA → public endpoint.
/// </summary>
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public class RequiresPermissionAttribute : Attribute
{
    public string Method  { get; }
    public string ApiPath { get; }

    public RequiresPermissionAttribute(string method, string apiPath)
    {
        Method  = method.ToUpper();
        ApiPath = apiPath.ToLower();
    }
}

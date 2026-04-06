using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ProfileService.Models.Request;
using ProfileService.Models.Response;
using ProfileService.Services.Interface;
using System.Security.Claims;

namespace ProfileService.Controllers;

[ApiController]
[Route("api/v1/customers")]
[Authorize]
public class CustomersController : ControllerBase
{
    private readonly ICustomerService _customerService;

    public CustomersController(ICustomerService customerService)
    {
        _customerService = customerService;
    }

    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User trong token.");
        return Guid.Parse(sub);
    }

    // GET /api/v1/customers?searchTerm=john&type=CANDIDATE&pageNumber=1&pageSize=10
    [HttpGet]
    [ApiMessage("Lấy danh sách hồ sơ thành công")]
    [RequiresPermission("GET", "/api/v1/customers")]
    public async Task<ActionResult<ResultPaginationDto<CustomerResponse>>> GetAll([FromQuery] CustomerFilterRequest filter)
    {
        var result = await _customerService.GetAllAsync(filter);
        return Ok(result);
    }

    // GET /api/v1/customers/me
    [HttpGet("me")]
    [ApiMessage("Lấy hồ sơ cá nhân thành công")]
    public async Task<ActionResult<CustomerResponse>> GetMyProfile()
    {
        return Ok(await _customerService.GetMyProfileAsync(GetCurrentUserId()));
    }

    // GET /api/v1/customers/{id}
    [HttpGet("{id:guid}")]
    [ApiMessage("Lấy hồ sơ thành công")]
    [RequiresPermission("GET", "/api/v1/customers/{id}")]
    public async Task<ActionResult<CustomerResponse>> GetProfileById(Guid id)
    {
        return Ok(await _customerService.GetProfileByIdAsync(id));
    }

    // PUT /api/v1/customers/me
    [HttpPut("me")]
    [ApiMessage("Cập nhật hồ sơ thành công")]
    public async Task<ActionResult<CustomerResponse>> UpdateMyProfile([FromBody] UpdateCustomerRequest request)
    {
        return Ok(await _customerService.UpdateMyProfileAsync(GetCurrentUserId(), request));
    }
}

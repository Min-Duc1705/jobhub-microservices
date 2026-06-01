using CommonService.Annotations;
using CommonService.Common;
using CommonService.File;
using CommonService.Filters;
using CommonService.Exceptions;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using ProfileService.Models.Request;
using ProfileService.Models.Response;
using ProfileService.Services.Interface;
using System.Security.Claims;
using MassTransit;
using CommonService.Events;

namespace ProfileService.Controllers;

[ApiController]
[Route("api/v1/customers")]
[Authorize]
public class CustomersController : ControllerBase
{
    private readonly ICustomerService _customerService;
    private readonly IFileService     _fileService;
    private readonly IPublishEndpoint _publishEndpoint;

    public CustomersController(
        ICustomerService customerService, 
        IFileService fileService,
        IPublishEndpoint publishEndpoint)
    {
        _customerService = customerService;
        _fileService     = fileService;
        _publishEndpoint = publishEndpoint;
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
    [RequiresPermission("GET", "/api/v1/customers/me")]
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
        CustomerResponse profile;
        try
        {
            profile = await _customerService.GetProfileByIdAsync(id);
        }
        catch (NotFoundException)
        {
            // Nếu không tìm thấy theo CustomerId, thử tìm theo AppUserId (userId tài khoản)
            profile = await _customerService.GetMyProfileAsync(id);
        }

        var viewerId = GetCurrentUserId();
        if (profile != null && viewerId != profile.AppUserId)
        {
            await _publishEndpoint.Publish(new SendNotificationEvent
            {
                UserId = profile.AppUserId,
                Title = "Hồ sơ của bạn đã được xem",
                Message = "Một nhà tuyển dụng đã xem hồ sơ của bạn.",
                Type = "view"
            });
        }
        return Ok(profile);
    }

    // PUT /api/v1/customers/me
    [HttpPut("me")]
    [ApiMessage("Cập nhật hồ sơ thành công")]
    [RequiresPermission("PUT", "/api/v1/customers/me")]
    public async Task<ActionResult<CustomerResponse>> UpdateMyProfile([FromBody] UpdateCustomerRequest request)
    {
        return Ok(await _customerService.UpdateMyProfileAsync(GetCurrentUserId(), request));
    }

    // POST /api/v1/customers/upload-avatar
    [HttpPost("upload-avatar")]
    [ApiMessage("Tải ảnh đại diện lên thành công")]
    [RequiresPermission("POST", "/api/v1/customers/upload-avatar")]
    public async Task<ActionResult<object>> UploadAvatar(IFormFile file)
    {
        var result = await _fileService.UploadAsync(
            file,
            bucketName:        "avatars",
            allowedExtensions: [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            maxSizeBytes:      5 * 1024 * 1024);   // 5 MB

        return Ok(new { Url = result.Url, ObjectName = result.ObjectName });
    }

    // PUT /api/v1/customers/{id}  — Admin update bất kỳ profile
    [HttpPut("{id:guid}")]
    [ApiMessage("Cập nhật hồ sơ thành công")]
    [RequiresPermission("PUT", "/api/v1/customers/{id}")]
    public async Task<ActionResult<CustomerResponse>> AdminUpdateCustomer(Guid id, [FromBody] UpdateCustomerRequest request)
    {
        return Ok(await _customerService.AdminUpdateCustomerAsync(id, request));
    }

    // DELETE /api/v1/customers/{id}  — Admin xóa profile
    [HttpDelete("{id:guid}")]
    [ApiMessage("Xóa hồ sơ thành công")]
    [RequiresPermission("DELETE", "/api/v1/customers/{id}")]
    public async Task<IActionResult> AdminDeleteCustomer(Guid id)
    {
        await _customerService.AdminDeleteCustomerAsync(id);
        return NoContent();
    }
}

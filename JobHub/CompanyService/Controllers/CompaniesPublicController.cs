using CommonService.Annotations;
using CommonService.Common;
using CommonService.File;
using CompanyService.Models.Request;
using CompanyService.Models.Response;
using CompanyService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CompanyService.Controllers;

/// <summary>
/// Các endpoint công khai dành cho người dùng thông thường (Employer).
/// Không yêu cầu quyền hạn đặc biệt, chỉ cần đăng nhập.
/// Route gốc: /api/v1/companies/public
/// </summary>
[ApiController]
[Route("api/v1/companies/public")]
[Authorize]
public class CompaniesPublicController : ControllerBase
{
    private readonly ICompanyService  _companyService;
    private readonly IFileService     _fileService;

    public CompaniesPublicController(
        ICompanyService companyService,
        IFileService    fileService)
    {
        _companyService = companyService;
        _fileService    = fileService;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // GET /api/v1/companies/public — chỉ trả về công ty ĐÃ XÁC MINH.
    // Dùng cho client-side (dropdown chọn công ty, trang danh sách công khai).
    // ─────────────────────────────────────────────────────────────────────────
    [HttpGet]
    [AllowAnonymous]
    [ApiMessage("Lấy danh sách công ty đã xác minh thành công")]
    public async Task<ActionResult<ResultPaginationDto<CompanyResponse>>> GetVerified(
        [FromQuery] CompanyFilterRequest filter)
    {
        filter.IsVerified = true;          // ép chỉ lấy công ty đã xác minh
        var result = await _companyService.GetAllAsync(filter);
        return Ok(result);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // POST /api/v1/companies/public/register
    // Employer tự đăng ký công ty, IsVerified = false — chờ Admin duyệt.
    // ─────────────────────────────────────────────────────────────────────────
    [HttpPost("register")]
    [ApiMessage("Đăng ký công ty thành công. Vui lòng chờ Admin xác minh trước khi hiển thị công khai.")]
    public async Task<ActionResult<CompanyResponse>> Register([FromBody] CreateCompanyRequest request)
    {
        var result = await _companyService.CreateAsync(request);
        return StatusCode(201, result);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // POST /api/v1/companies/public/upload
    // Employer tự upload logo / ảnh bìa mà không cần quyền Admin.
    // ─────────────────────────────────────────────────────────────────────────
    [HttpPost("upload")]
    [ApiMessage("Tải ảnh lên thành công")]
    public async Task<ActionResult<object>> Upload(IFormFile file)
    {
        var result = await _fileService.UploadAsync(
            file,
            bucketName:        "companies",
            allowedExtensions: [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            maxSizeBytes:      10 * 1024 * 1024);   // 10 MB

        return Ok(new { url = result.Url });
    }
}

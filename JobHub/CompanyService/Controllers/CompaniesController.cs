using CommonService.Annotations;
using CommonService.Common;
using CommonService.File;
using CommonService.Filters;
using CompanyService.Models.Request;
using CompanyService.Models.Response;
using CompanyService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace CompanyService.Controllers;

[ApiController]
[Route("api/v1/companies")]
[Authorize]
public class CompaniesController : ControllerBase
{
    private readonly ICompanyService _companyService;
    private readonly IFileService     _fileService;

    public CompaniesController(ICompanyService companyService, IFileService fileService)
    {
        _companyService = companyService;
        _fileService    = fileService;
    }

    // GET /api/v1/companies?searchTerm=...&industry=IT&pageNumber=1&pageSize=10
    [HttpGet]
    [AllowAnonymous]
    [ApiMessage("Lấy danh sách công ty thành công")]
    public async Task<ActionResult<ResultPaginationDto<CompanyResponse>>> GetAll(
        [FromQuery] CompanyFilterRequest filter)
    {
        var result = await _companyService.GetAllAsync(filter);
        return Ok(result);
    }

    // GET /api/v1/companies/{id}
    [HttpGet("{id:guid}")]
    [AllowAnonymous]
    [ApiMessage("Lấy thông tin công ty thành công")]
    public async Task<ActionResult<CompanyResponse>> GetById(Guid id)
    {
        return Ok(await _companyService.GetByIdAsync(id));
    }

    // POST /api/v1/companies   (Admin only)
    [HttpPost]
    [ApiMessage("Tạo công ty thành công")]
    [RequiresPermission("POST", "/api/v1/companies")]
    public async Task<ActionResult<CompanyResponse>> Create([FromBody] CreateCompanyRequest request)
    {
        var result = await _companyService.CreateAsync(request);
        return StatusCode(201, result);
    }

    // PUT /api/v1/companies/{id}
    [HttpPut("{id:guid}")]
    [ApiMessage("Cập nhật công ty thành công")]
    [RequiresPermission("PUT", "/api/v1/companies/{id}")]
    public async Task<ActionResult<CompanyResponse>> Update(Guid id, [FromBody] UpdateCompanyRequest request)
    {
        return Ok(await _companyService.UpdateAsync(id, request));
    }

    // DELETE /api/v1/companies/{id}
    [HttpDelete("{id:guid}")]
    [ApiMessage("Xóa công ty thành công")]
    [RequiresPermission("DELETE", "/api/v1/companies/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _companyService.DeleteAsync(id);
        return Ok((object?)null);
    }

    // PATCH /api/v1/companies/{id}/verify
    [HttpPatch("{id:guid}/verify")]
    [ApiMessage("Xác minh công ty thành công")]
    [RequiresPermission("PATCH", "/api/v1/companies/{id}/verify")]
    public async Task<ActionResult<CompanyResponse>> Verify(Guid id)
    {
        return Ok(await _companyService.VerifyAsync(id));
    }

    // POST /api/v1/companies/upload
    [HttpPost("upload")]
    [ApiMessage("Tải ảnh lên thành công")]
    [RequiresPermission("POST", "/api/v1/companies/upload")]
    public async Task<ActionResult<object>> Upload(IFormFile file)
    {
        var result = await _fileService.UploadAsync(
            file,
            bucketName:         "companies",
            allowedExtensions:  [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            maxSizeBytes:       10 * 1024 * 1024);   // 10 MB

        return Ok(new { url = result.Url });
    }
}

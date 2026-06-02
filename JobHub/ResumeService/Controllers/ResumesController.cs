using CommonService.Annotations;
using CommonService.Common;
using CommonService.File;
using CommonService.Filters;
using ResumeService.Models.Request;
using ResumeService.Models.Response;
using ResumeService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using SautinSoft.Document;
using System.IO;
using System.Security.Claims;

namespace ResumeService.Controllers;

[ApiController]
[Route("api/v1/resumes")]
public class ResumesController : ControllerBase
{
    private readonly IResumeService _resumeService;
    private readonly IFileService   _fileService;
    private readonly IResumeTextExtractionService _resumeTextExtractionService;

    public ResumesController(
        IResumeService resumeService,
        IFileService fileService,
        IResumeTextExtractionService resumeTextExtractionService)
    {
        _resumeService = resumeService;
        _fileService   = fileService;
        _resumeTextExtractionService = resumeTextExtractionService;
    }

    // GET /api/v1/resumes (lấy danh sách CV, có thể filter theo customerId)
    [HttpGet]
    [Authorize]
    [ApiMessage("Lấy danh sách CV thành công")]
    [RequiresPermission("GET", "/api/v1/resumes")]
    public async Task<ActionResult<ResultPaginationDto<ResumeResponse>>> GetAll(
        [FromQuery] ResumeFilterRequest filter)
        => Ok(await _resumeService.GetAllAsync(filter));

    // GET /api/v1/resumes/{id}
    [HttpGet("{id:guid}")]
    [Authorize]
    [ApiMessage("Lấy thông tin CV thành công")]
    [RequiresPermission("GET", "/api/v1/resumes/{id}")]
    public async Task<ActionResult<ResumeResponse>> GetById(Guid id)
        => Ok(await _resumeService.GetByIdAsync(id));

    // POST /api/v1/resumes (Ứng viên tạo CV mới)
    [HttpPost]
    [Authorize]
    [ApiMessage("Tạo CV thành công")]
    [RequiresPermission("POST", "/api/v1/resumes")]
    public async Task<ActionResult<ResumeResponse>> Create([FromBody] CreateResumeRequest request)
    {
        var customerId = GetCurrentUserId();
        var result = await _resumeService.CreateAsync(customerId, request);
        return StatusCode(201, result);
    }

    // PUT /api/v1/resumes/{id}
    [HttpPut("{id:guid}")]
    [Authorize]
    [ApiMessage("Cập nhật CV thành công")]
    [RequiresPermission("PUT", "/api/v1/resumes/{id}")]
    public async Task<ActionResult<ResumeResponse>> Update(Guid id, [FromBody] UpdateResumeRequest request)
        => Ok(await _resumeService.UpdateAsync(id, request));

    // DELETE /api/v1/resumes/{id}
    [HttpDelete("{id:guid}")]
    [Authorize]
    [ApiMessage("Xóa CV thành công")]
    [RequiresPermission("DELETE", "/api/v1/resumes/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _resumeService.DeleteAsync(id);
        return Ok((object?)null);
    }

    // PATCH /api/v1/resumes/{id}/set-default (Ứng viên đặt CV mặc định)
    [HttpPatch("{id:guid}/set-default")]
    [Authorize]
    [ApiMessage("Đặt CV mặc định thành công")]
    [RequiresPermission("PATCH", "/api/v1/resumes/{id}/set-default")]
    public async Task<IActionResult> SetDefault(Guid id)
    {
        var customerId = GetCurrentUserId();
        await _resumeService.SetDefaultAsync(customerId, id);
        return Ok((object?)null);
    }

    // POST /api/v1/resumes/online (Tạo Online CV qua Builder)
    [HttpPost("online")]
    [Authorize]
    [ApiMessage("Tạo Online CV thành công")]
    [RequiresPermission("POST", "/api/v1/resumes/online")]
    public async Task<ActionResult<ResumeResponse>> CreateOnline([FromBody] CreateOnlineCvRequest request)
    {
        var customerId = GetCurrentUserId();
        var result = await _resumeService.CreateOnlineAsync(customerId, request);
        return StatusCode(201, result);
    }

    // PUT /api/v1/resumes/{id}/content (Auto-save nội dung CV)
    [HttpPut("{id:guid}/content")]
    [Authorize]
    [ApiMessage("Lưu nội dung CV thành công")]
    [RequiresPermission("PUT", "/api/v1/resumes/{id}/content")]
    public async Task<ActionResult<ResumeResponse>> UpdateContent(Guid id, [FromBody] UpdateCvContentRequest request)
    {
        var customerId = GetCurrentUserId();
        return Ok(await _resumeService.UpdateContentAsync(id, customerId, request));
    }

    // POST /api/v1/resumes/upload
    [HttpPost("upload")]
    [Authorize]
    [ApiMessage("Upload CV thành công")]
    public async Task<ActionResult<object>> UploadCv(IFormFile file)
    {
        var result = await _fileService.UploadAsync(
            file,
            bucketName:        "resumes",
            allowedExtensions: [".pdf", ".doc", ".docx"],
            maxSizeBytes:      20 * 1024 * 1024);   // 20 MB

        string? extractedText = null;
        try
        {
            var ext = Path.GetExtension(file.FileName).ToLowerInvariant();
            if (ext == ".pdf" || ext == ".docx" || ext == ".doc")
            {
                extractedText = await _resumeTextExtractionService.ExtractAsync(file);
            }
        }
        catch (Exception ex)
        {
            // Bỏ qua lỗi trích xuất text để không làm gián đoạn luồng upload
            Console.WriteLine($"[TextExtraction] Lỗi khi trích xuất text từ file '{file.FileName}': {ex.Message}");
        }

        return Ok(new
        {
            Url = result.ObjectName,
            FullUrl = result.Url,
            OriginalFileName = result.OriginalFileName,
            ExtractedText = extractedText
        });
    }

    // GET /api/v1/resumes/{id}/preview
    [HttpGet("{id:guid}/preview")]
    [Authorize]
    public async Task<IActionResult> Preview(Guid id)
    {
        var resume = await _resumeService.GetByIdAsync(id);

        if (resume.IsOnlineCv || string.IsNullOrEmpty(resume.Url))
            return BadRequest("CV này không có file đính kèm.");

        var stream = await _fileService.DownloadAsync("resumes", resume.Url);

        if (resume.Url.EndsWith(".pdf", StringComparison.OrdinalIgnoreCase))
        {
            return File(stream, "application/pdf");
        }
        else if (resume.Url.EndsWith(".docx", StringComparison.OrdinalIgnoreCase) || 
                 resume.Url.EndsWith(".doc", StringComparison.OrdinalIgnoreCase))
        {
            try
            {
                var pdfStream = new MemoryStream();
                var loadOptions = resume.Url.EndsWith(".docx", StringComparison.OrdinalIgnoreCase)
                    ? (LoadOptions)new DocxLoadOptions()
                    : (LoadOptions)new DocLoadOptions();
                
                var doc = DocumentCore.Load(stream, loadOptions);
                doc.Save(pdfStream, new PdfSaveOptions());
                pdfStream.Position = 0;
                
                return File(pdfStream, "application/pdf");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[PDF-Preview-Conversion] Lỗi convert Word sang PDF cho {resume.Title} ({resume.Id}): {ex.Message}");
                // Fallback: trả về file Word gốc nếu convert lỗi
                if (stream.CanSeek) stream.Position = 0;
                var contentType = resume.Url.EndsWith(".docx", StringComparison.OrdinalIgnoreCase)
                    ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    : "application/msword";
                return File(stream, contentType);
            }
        }

        return File(stream, "application/octet-stream");
    }

    // GET /api/v1/resumes/{id}/download
    [HttpGet("{id:guid}/download")]
    [Authorize]
    public async Task<IActionResult> Download(Guid id)
    {
        var resume = await _resumeService.GetByIdAsync(id);

        if (resume.IsOnlineCv || string.IsNullOrEmpty(resume.Url))
            return BadRequest("CV này không có file đính kèm. Hãy dùng tính năng xuất PDF trên trình duyệt.");

        var stream = await _fileService.DownloadAsync("resumes", resume.Url);

        var contentType = "application/octet-stream";
        if (resume.Url.EndsWith(".pdf",  StringComparison.OrdinalIgnoreCase)) contentType = "application/pdf";
        else if (resume.Url.EndsWith(".docx", StringComparison.OrdinalIgnoreCase)) contentType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
        else if (resume.Url.EndsWith(".doc",  StringComparison.OrdinalIgnoreCase)) contentType = "application/msword";

        return File(stream, contentType);
    }

    // ── Helper ────────────────────────────────────────────────────────────────
    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không xác định được người dùng.");
        return Guid.Parse(sub);
    }
}

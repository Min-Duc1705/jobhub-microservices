using CommonService.Annotations;
using ResumeService.Models.Request;
using ResumeService.Models.Response;
using ResumeService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using System.Threading.Tasks;
using System;
using System.Collections.Generic;

namespace ResumeService.Controllers;

[ApiController]
[Route("api/v1/interviews")]
public class InterviewsController : ControllerBase
{
    private readonly IInterviewService _interviewService;

    public InterviewsController(IInterviewService interviewService)
    {
        _interviewService = interviewService;
    }

    [HttpGet]
    [Authorize]
    [ApiMessage("Lấy danh sách lịch phỏng vấn thành công")]
    public async Task<ActionResult<List<InterviewResponse>>> GetInterviews()
    {
        var currentUserId = GetCurrentUserId();
        
        // Phân quyền: Nếu là HR/Recruiter thì lấy lịch do họ tạo, nếu là ứng viên thì lấy lịch của họ
        var role = User.FindFirstValue(ClaimTypes.Role) ?? User.FindFirstValue("role") ?? "";
        
        // Do hệ thống có thể trả về các chuỗi hoa/thường khác nhau, ta so sánh không phân biệt hoa thường
        if (role.Equals("HR", StringComparison.OrdinalIgnoreCase) || 
            role.Equals("RECRUITER", StringComparison.OrdinalIgnoreCase) || 
            role.Contains("HR", StringComparison.OrdinalIgnoreCase) || 
            role.Contains("Recruiter", StringComparison.OrdinalIgnoreCase))
        {
            var list = await _interviewService.GetByRecruiterAsync(currentUserId);
            return Ok(list);
        }
        else
        {
            var list = await _interviewService.GetByCandidateAsync(currentUserId);
            return Ok(list);
        }
    }

    [HttpGet("{id:guid}")]
    [Authorize]
    [ApiMessage("Lấy thông tin chi tiết lịch phỏng vấn thành công")]
    public async Task<ActionResult<InterviewResponse>> GetById(Guid id)
    {
        var result = await _interviewService.GetByIdAsync(id);
        return Ok(result);
    }

    [HttpPost]
    [Authorize]
    [ApiMessage("Đặt lịch phỏng vấn thành công")]
    public async Task<ActionResult<InterviewResponse>> Create([FromBody] CreateInterviewRequest request)
    {
        var recruiterId = GetCurrentUserId();
        var result = await _interviewService.CreateAsync(recruiterId, request);
        return StatusCode(201, result);
    }

    [HttpPut("{id:guid}")]
    [Authorize]
    [ApiMessage("Cập nhật lịch phỏng vấn thành công")]
    public async Task<ActionResult<InterviewResponse>> Update(Guid id, [FromBody] UpdateInterviewRequest request)
    {
        var result = await _interviewService.UpdateAsync(id, request);
        return Ok(result);
    }

    [HttpDelete("{id:guid}")]
    [Authorize]
    [ApiMessage("Hủy lịch phỏng vấn thành công")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _interviewService.DeleteAsync(id);
        return Ok((object?)null);
    }

    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không xác định được người dùng.");
        return Guid.Parse(sub);
    }
}

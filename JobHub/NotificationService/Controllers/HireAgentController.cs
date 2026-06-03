using CommonService.Annotations;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NotificationService.Models.Request;
using NotificationService.Services.Interface;
using System;
using System.Security.Claims;
using System.Threading.Tasks;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/hire-agent")]
[Authorize]
public class HireAgentController : ControllerBase
{
    private readonly IHireAgentService _hireAgentService;

    public HireAgentController(IHireAgentService hireAgentService)
    {
        _hireAgentService = hireAgentService;
    }

    private string GetCurrentUserId()
    {
        return User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User trong token.");
    }

    [HttpPost("campaigns")]
    [ApiMessage("Tạo chiến dịch tuyển dụng AI thành công")]
    public async Task<IActionResult> CreateCampaign([FromBody] CreateHireAgentCampaignRequest request)
    {
        var recruiterId = GetCurrentUserId();
        var campaign = await _hireAgentService.CreateCampaignAsync(
            request.JobId,
            request.JobName,
            request.JobDescription,
            recruiterId,
            request.TargetCount
        );
        return Ok(campaign);
    }

    [HttpGet("campaigns")]
    [ApiMessage("Lấy danh sách chiến dịch tuyển dụng AI thành công")]
    public async Task<IActionResult> GetCampaigns()
    {
        var recruiterId = GetCurrentUserId();
        var list = await _hireAgentService.GetCampaignsByRecruiterAsync(recruiterId);
        return Ok(list);
    }

    [HttpGet("campaigns/{campaignId:guid}/conversations")]
    [ApiMessage("Lấy danh sách ứng viên sàng lọc thành công")]
    public async Task<IActionResult> GetConversations(Guid campaignId)
    {
        var list = await _hireAgentService.GetConversationsByCampaignAsync(campaignId);
        return Ok(list);
    }

    [HttpGet("campaigns/{campaignId:guid}")]
    [ApiMessage("Lấy thông tin chiến dịch tuyển dụng AI thành công")]
    public async Task<IActionResult> GetCampaign(Guid campaignId)
    {
        var campaign = await _hireAgentService.GetCampaignByIdAsync(campaignId);
        if (campaign == null)
        {
            return NotFound("Không tìm thấy chiến dịch tuyển dụng.");
        }
        return Ok(campaign);
    }

    [HttpPost("campaigns/{campaignId:guid}/schedule")]
    [ApiMessage("Đặt lịch hẹn phỏng vấn thành công")]
    public async Task<IActionResult> ScheduleInterview(Guid campaignId, [FromBody] ScheduleInterviewRequest request)
    {
        var candidateId = GetCurrentUserId();
        var conversation = await _hireAgentService.ScheduleInterviewAsync(campaignId, candidateId, request.InterviewDate);
        return Ok(conversation);
    }
}

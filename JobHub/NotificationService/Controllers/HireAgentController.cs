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
            request.TargetCount,
            request.JobLocation,
            request.JobType,
            request.InterviewDate,
            request.BackupInterviewDate
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

    /// <summary>HR đặt lịch đề xuất phỏng vấn → candidate nhận thông báo và xác nhận</summary>
    [HttpPost("campaigns/{campaignId:guid}/schedule")]
    [ApiMessage("Đề xuất lịch hẹn phỏng vấn thành công")]
    public async Task<IActionResult> ScheduleInterview(Guid campaignId, [FromBody] ScheduleInterviewRequest request)
    {
        // HR lấy candidateId từ request body vì HR đặt lịch cho candidate cụ thể
        if (string.IsNullOrEmpty(request.CandidateId))
            return BadRequest("CandidateId là bắt buộc.");

        var conversation = await _hireAgentService.ScheduleInterviewAsync(campaignId, request.CandidateId, request.InterviewDate);
        return Ok(conversation);
    }

    /// <summary>Candidate xác nhận đồng ý lịch phỏng vấn HR đề xuất</summary>
    [HttpPost("campaigns/{campaignId:guid}/confirm")]
    [ApiMessage("Xác nhận lịch hẹn phỏng vấn thành công")]
    public async Task<IActionResult> ConfirmInterview(Guid campaignId)
    {
        var candidateId = GetCurrentUserId();
        var conversation = await _hireAgentService.ConfirmInterviewAsync(campaignId, candidateId);
        return Ok(conversation);
    }

    /// <summary>Candidate đề xuất đổi lịch → thông báo HR, reset về Passed</summary>
    [HttpPost("campaigns/{campaignId:guid}/propose-reschedule")]
    [ApiMessage("Đề xuất đổi lịch phỏng vấn thành công")]
    public async Task<IActionResult> ProposeReschedule(Guid campaignId, [FromBody] ProposeRescheduleRequest request)
    {
        var candidateId = GetCurrentUserId();
        var conversation = await _hireAgentService.ProposeRescheduleAsync(campaignId, candidateId, request.Message);
        return Ok(conversation);
    }

    /// <summary>HR hủy lịch hẹn phỏng vấn → thông báo ứng viên, reset về Passed và xóa ngày</summary>
    [HttpPost("campaigns/{campaignId:guid}/cancel-schedule")]
    [ApiMessage("Hủy lịch phỏng vấn thành công")]
    public async Task<IActionResult> CancelInterview(Guid campaignId, [FromBody] CancelInterviewRequest request)
    {
        if (string.IsNullOrEmpty(request.CandidateId))
            return BadRequest("CandidateId là bắt buộc.");

        var conversation = await _hireAgentService.CancelInterviewAsync(campaignId, request.CandidateId);
        return Ok(conversation);
    }

    [HttpGet("campaigns/{campaignId:guid}/my-conversation")]
    [ApiMessage("Lấy thông tin hội thoại phỏng vấn của ứng viên thành công")]
    public async Task<IActionResult> GetMyConversation(Guid campaignId)
    {
        var candidateId = GetCurrentUserId();
        var conversation = await _hireAgentService.GetConversationByCandidateAndCampaignAsync(campaignId, candidateId);
        if (conversation == null)
        {
            return NotFound("Không tìm thấy cuộc hội thoại tuyển dụng AI.");
        }
        return Ok(conversation);
    }
}

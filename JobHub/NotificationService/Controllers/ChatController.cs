using CommonService.Annotations;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NotificationService.Models.Response;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Security.Claims;
using System.Threading.Tasks;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/chat")]
[Authorize]
public class ChatController : ControllerBase
{
    private readonly IChatService _chatService;

    public ChatController(IChatService chatService)
    {
        _chatService = chatService;
    }

    private string GetCurrentUserId()
    {
        return User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User trong token.");
    }

    // GET /api/v1/chat/conversations
    [HttpGet("conversations")]
    [ApiMessage("Lấy danh sách cuộc hội thoại thành công")]
    public async Task<ActionResult<List<ConversationResponse>>> GetConversations()
    {
        var userId = GetCurrentUserId();
        var result = await _chatService.GetConversationsForUserAsync(userId);
        return Ok(result);
    }

    // GET /api/v1/chat/conversations/{conversationId}/messages
    [HttpGet("conversations/{conversationId:guid}/messages")]
    [ApiMessage("Lấy lịch sử tin nhắn thành công")]
    public async Task<ActionResult<List<MessageResponse>>> GetChatHistory(
        Guid conversationId,
        [FromQuery] int limit = 50,
        [FromQuery] DateTimeOffset? before = null)
    {
        var userId = GetCurrentUserId();
        var result = await _chatService.GetChatHistoryAsync(userId, conversationId, limit, before);
        return Ok(result);
    }

    // POST /api/v1/chat/conversations/get-or-create
    [HttpPost("conversations/get-or-create")]
    [ApiMessage("Lấy hoặc tạo cuộc hội thoại thành công")]
    public async Task<ActionResult<ConversationResponse>> GetOrCreateConversation([FromBody] GetOrCreateConversationRequest request)
    {
        var userId = GetCurrentUserId();
        var result = await _chatService.GetOrCreateConversationAsync(userId, request.OtherParticipantId);
        return Ok(result);
    }

    // POST /api/v1/chat/messages
    [HttpPost("messages")]
    [ApiMessage("Gửi tin nhắn thành công")]
    public async Task<ActionResult<MessageResponse>> SendMessage([FromBody] SendMessageRequest request)
    {
        var userId = GetCurrentUserId();
        var result = await _chatService.SendMessageAsync(userId, request.ReceiverId, request.Content, request.Type);
        return Ok(result);
    }

    // POST /api/v1/chat/conversations/{conversationId}/messages
    [HttpPost("conversations/{conversationId:guid}/messages")]
    [ApiMessage("Gửi tin nhắn thành công")]
    public async Task<ActionResult<MessageResponse>> SendMessageToConversation(
        Guid conversationId,
        [FromBody] SendMessageToConversationRequest request)
    {
        var userId = GetCurrentUserId();
        var result = await _chatService.SendMessageToConversationAsync(userId, conversationId, request.Content, request.Type);
        return Ok(result);
    }
}

public class GetOrCreateConversationRequest
{
    public string OtherParticipantId { get; set; } = string.Empty;
}

public class SendMessageRequest
{
    public string ReceiverId { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Type { get; set; } = "text";
}

public class SendMessageToConversationRequest
{
    public string Content { get; set; } = string.Empty;
    public string Type { get; set; } = "text";
}

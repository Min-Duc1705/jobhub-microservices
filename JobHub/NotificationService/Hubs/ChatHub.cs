using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.SignalR;
using NotificationService.Services.Interface;
using System;
using System.Security.Claims;
using System.Threading.Tasks;

namespace NotificationService.Hubs;

[Authorize]
public class ChatHub : Hub
{
    private readonly IChatService _chatService;

    public ChatHub(IChatService chatService)
    {
        _chatService = chatService;
    }

    private string? GetUserId()
    {
        return Context.User?.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? Context.User?.FindFirstValue("sub")
               ?? Context.User?.FindFirstValue("UserId");
    }

    public override async Task OnConnectedAsync()
    {
        var userId = GetUserId();
        if (!string.IsNullOrEmpty(userId))
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, userId.ToLower());
        }
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        var userId = GetUserId();
        if (!string.IsNullOrEmpty(userId))
        {
            await Groups.RemoveFromGroupAsync(Context.ConnectionId, userId.ToLower());
        }
        await base.OnDisconnectedAsync(exception);
    }

    // Client gọi hàm này để gửi tin nhắn cá nhân
    public async Task SendPrivateMessage(string receiverId, string content, string type = "text")
    {
        var senderId = GetUserId();
        if (string.IsNullOrEmpty(senderId))
        {
            throw new HubException("Unauthorized.");
        }

        if (string.IsNullOrWhiteSpace(receiverId))
        {
            throw new HubException("ReceiverId is required.");
        }

        // 1. Lưu tin nhắn vào DB thông qua service
        var message = await _chatService.SendMessageAsync(senderId, receiverId, content, type);

        // 2. Gửi tin nhắn real-time tới Group của người nhận
        await Clients.Group(receiverId.ToLower()).SendAsync("ReceiveMessage", message);

        // 3. Gửi tin nhắn về Caller (chính người gửi) để xác nhận thành công
        await Clients.Caller.SendAsync("ReceiveMessage", message);
    }

    // Client gọi hàm này để báo rằng đã đọc hết tin nhắn trong cuộc hội thoại
    public async Task MarkConversationAsRead(string conversationIdStr, string otherParticipantId)
    {
        var userId = GetUserId();
        if (string.IsNullOrEmpty(userId))
        {
            throw new HubException("Unauthorized.");
        }

        if (Guid.TryParse(conversationIdStr, out var conversationId))
        {
            // 1. Đánh dấu đã đọc trong Database
            await _chatService.MarkAsReadAsync(userId, conversationId);

            // 2. Phát sự kiện "đã đọc" tới cả hai bên
            // - Người đọc: để các kết nối khác (như HeaderClient) nhận diện và cập nhật giảm badge số lượng tin nhắn chưa đọc
            // - Người gửi: để cập nhật trạng thái tích xanh (tin nhắn đã đọc)
            await Clients.Group(userId.ToLower()).SendAsync("ConversationRead", new
            {
                ConversationId = conversationId,
                ReaderId = userId
            });

            await Clients.Group(otherParticipantId.ToLower()).SendAsync("ConversationRead", new
            {
                ConversationId = conversationId,
                ReaderId = userId
            });
        }
    }
}

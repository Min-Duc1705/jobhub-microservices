using CommonService.Events;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using NotificationService.Data;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace NotificationService.Consumers;

public class NotificationUserDeletedConsumer : IConsumer<UserDeletedEvent>
{
    private readonly NotificationDbContext _dbContext;
    private readonly ILogger<NotificationUserDeletedConsumer> _logger;

    public NotificationUserDeletedConsumer(NotificationDbContext dbContext, ILogger<NotificationUserDeletedConsumer> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task Consume(ConsumeContext<UserDeletedEvent> context)
    {
        var message = context.Message;
        _logger.LogInformation("Nhận được sự kiện xóa User từ Auth: {UserId}", message.UserId);

        using var transaction = await _dbContext.Database.BeginTransactionAsync();
        try
        {
            var now = DateTimeOffset.UtcNow;
            var userIdStr = message.UserId.ToString();

            // 1. Soft-delete Notifications
            var notifications = await _dbContext.Notifications
                .IgnoreQueryFilters()
                .Where(n => n.AppUserId == message.UserId && !n.IsDeleted)
                .ToListAsync();

            foreach (var notif in notifications)
            {
                notif.IsDeleted = true;
                notif.DeletedAt = now;
            }
            if (notifications.Any())
            {
                _logger.LogInformation("Đã soft-delete {Count} Notifications cho AppUser {UserId}", notifications.Count, message.UserId);
            }

            // 2. Soft-delete HireAgentCampaigns
            var campaigns = await _dbContext.HireAgentCampaigns
                .IgnoreQueryFilters()
                .Where(c => c.RecruiterId == userIdStr && !c.IsDeleted)
                .ToListAsync();

            foreach (var campaign in campaigns)
            {
                campaign.IsDeleted = true;
                campaign.DeletedAt = now;
            }
            if (campaigns.Any())
            {
                _logger.LogInformation("Đã soft-delete {Count} HireAgentCampaigns cho Recruiter {UserId}", campaigns.Count, message.UserId);
            }

            // 3. Soft-delete HireAgentConversations
            var hireConversations = await _dbContext.HireAgentConversations
                .IgnoreQueryFilters()
                .Where(hc => hc.CandidateId == userIdStr && !hc.IsDeleted)
                .ToListAsync();

            foreach (var hc in hireConversations)
            {
                hc.IsDeleted = true;
                hc.DeletedAt = now;
            }
            if (hireConversations.Any())
            {
                _logger.LogInformation("Đã soft-delete {Count} HireAgentConversations cho Candidate {UserId}", hireConversations.Count, message.UserId);
            }

            // 4. Soft-delete Conversations & Messages
            var conversations = await _dbContext.Conversations
                .IgnoreQueryFilters()
                .Where(c => (c.ParticipantA == userIdStr || c.ParticipantB == userIdStr) && !c.IsDeleted)
                .ToListAsync();

            if (conversations.Any())
            {
                foreach (var conv in conversations)
                {
                    conv.IsDeleted = true;
                    conv.DeletedAt = now;
                }

                var convIds = conversations.Select(c => c.Id).ToList();
                var messages = await _dbContext.Messages
                    .IgnoreQueryFilters()
                    .Where(m => convIds.Contains(m.ConversationId) && !m.IsDeleted)
                    .ToListAsync();

                foreach (var msg in messages)
                {
                    msg.IsDeleted = true;
                    msg.DeletedAt = now;
                }

                _logger.LogInformation("Đã soft-delete {ConvCount} Conversations và {MsgCount} Messages cho AppUser {UserId}", 
                    conversations.Count, messages.Count, message.UserId);
            }

            await _dbContext.SaveChangesAsync();
            await transaction.CommitAsync();
        }
        catch (Exception ex)
        {
            await transaction.RollbackAsync();
            _logger.LogError(ex, "Lỗi khi xử lý xóa dữ liệu liên quan trong NotificationService cho AppUser {UserId}", message.UserId);
            throw;
        }
    }
}

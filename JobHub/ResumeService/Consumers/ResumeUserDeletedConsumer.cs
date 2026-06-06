using CommonService.Events;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using ResumeService.Data;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace ResumeService.Consumers;

public class ResumeUserDeletedConsumer : IConsumer<UserDeletedEvent>
{
    private readonly ResumeDbContext _dbContext;
    private readonly ILogger<ResumeUserDeletedConsumer> _logger;

    public ResumeUserDeletedConsumer(ResumeDbContext dbContext, ILogger<ResumeUserDeletedConsumer> logger)
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

            // 1. Soft-delete các Application của Customer trước
            var applications = await _dbContext.Applications
                .IgnoreQueryFilters()
                .Where(a => a.CustomerId == message.UserId && !a.IsDeleted)
                .ToListAsync();

            foreach (var app in applications)
            {
                app.IsDeleted = true;
                app.DeletedAt = now;
            }

            // 2. Soft-delete các Resume của Customer
            var resumes = await _dbContext.Resumes
                .IgnoreQueryFilters()
                .Where(r => r.CustomerId == message.UserId && !r.IsDeleted)
                .ToListAsync();

            foreach (var resume in resumes)
            {
                resume.IsDeleted = true;
                resume.DeletedAt = now;
            }

            if (applications.Any() || resumes.Any())
            {
                await _dbContext.SaveChangesAsync();
                _logger.LogInformation("Đã soft-delete {AppCount} Applications và {ResumeCount} Resumes cho AppUser {UserId}", 
                    applications.Count, resumes.Count, message.UserId);
            }
            else
            {
                _logger.LogInformation("Không tìm thấy Applications hay Resumes nào cho AppUser {UserId} để xóa.", message.UserId);
            }

            await transaction.CommitAsync();
        }
        catch (Exception ex)
        {
            await transaction.RollbackAsync();
            _logger.LogError(ex, "Lỗi khi thực hiện xóa Applications và Resumes cho AppUser {UserId}", message.UserId);
            throw;
        }
    }
}

using CommonService.Events;
using JobService.Data;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace JobService.Consumers;

public class JobUserDeletedConsumer : IConsumer<UserDeletedEvent>
{
    private readonly JobDbContext _dbContext;
    private readonly ILogger<JobUserDeletedConsumer> _logger;

    public JobUserDeletedConsumer(JobDbContext dbContext, ILogger<JobUserDeletedConsumer> logger)
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

            // 1. Nếu user là Candidate: Xóa các SavedJob đã lưu
            var savedJobs = await _dbContext.SavedJobs
                .Where(sv => sv.CustomerId == message.UserId)
                .ToListAsync();

            if (savedJobs.Any())
            {
                _dbContext.SavedJobs.RemoveRange(savedJobs);
                _logger.LogInformation("Đã hard-delete {Count} SavedJobs cho Candidate {UserId}", savedJobs.Count, message.UserId);
            }

            // 2. Nếu user là Employer/HR: Soft-delete các Job đã đăng
            var jobs = await _dbContext.Jobs
                .IgnoreQueryFilters()
                .Where(j => j.CustomerId == message.UserId && !j.IsDeleted)
                .ToListAsync();

            if (jobs.Any())
            {
                foreach (var job in jobs)
                {
                    job.IsDeleted = true;
                    job.DeletedAt = now;
                }
                _logger.LogInformation("Đã soft-delete {Count} Jobs cho HR {UserId}", jobs.Count, message.UserId);
            }

            if (savedJobs.Any() || jobs.Any())
            {
                await _dbContext.SaveChangesAsync();
            }
            else
            {
                _logger.LogInformation("Không tìm thấy Jobs hay SavedJobs nào cho AppUser {UserId} để xử lý.", message.UserId);
            }

            await transaction.CommitAsync();
        }
        catch (Exception ex)
        {
            await transaction.RollbackAsync();
            _logger.LogError(ex, "Lỗi khi xử lý xóa Jobs/SavedJobs cho AppUser {UserId}", message.UserId);
            throw;
        }
    }
}

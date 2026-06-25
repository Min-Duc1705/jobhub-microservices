using CommonService.Events;
using JobService.Data;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace JobService.Consumers;

public class CompanyUpdatedConsumer : IConsumer<CompanyUpdatedEvent>
{
    private readonly JobDbContext _dbContext;
    private readonly ILogger<CompanyUpdatedConsumer> _logger;

    public CompanyUpdatedConsumer(JobDbContext dbContext, ILogger<CompanyUpdatedConsumer> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task Consume(ConsumeContext<CompanyUpdatedEvent> context)
    {
        var message = context.Message;
        _logger.LogInformation("Nhận được sự kiện cập nhật Company từ CompanyService: {CompanyName} (ID: {CompanyId})", message.Name, message.Id);

        try
        {
            var jobs = await _dbContext.Jobs
                .IgnoreQueryFilters()
                .Where(j => j.CompanyId == message.Id)
                .ToListAsync();

            if (jobs.Any())
            {
                foreach (var job in jobs)
                {
                    job.CompanyName = message.Name;
                    job.CompanyLogo = message.Logo;
                }

                await _dbContext.SaveChangesAsync();
                _logger.LogInformation("Đã cập nhật CompanyName/CompanyLogo cho {Count} jobs liên quan đến CompanyId {CompanyId}", jobs.Count, message.Id);
            }
            else
            {
                _logger.LogInformation("Không tìm thấy jobs nào cho CompanyId {CompanyId} để cập nhật.", message.Id);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Lỗi khi cập nhật jobs cho CompanyId {CompanyId}", message.Id);
            throw;
        }
    }
}

using CommonService.Events;
using JobService.Repositories.Interface;
using MassTransit;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Threading.Tasks;

namespace JobService.Consumers;

public class ApplicationSubmittedConsumer : IConsumer<ApplicationSubmittedEvent>
{
    private readonly IJobRepository _jobRepo;
    private readonly IConfiguration _configuration;
    private readonly ILogger<ApplicationSubmittedConsumer> _logger;

    public ApplicationSubmittedConsumer(
        IJobRepository jobRepo,
        IConfiguration configuration,
        ILogger<ApplicationSubmittedConsumer> logger)
    {
        _jobRepo = jobRepo;
        _configuration = configuration;
        _logger = logger;
    }

    public async Task Consume(ConsumeContext<ApplicationSubmittedEvent> context)
    {
        var msg = context.Message;
        _logger.LogInformation("JobService nhận được ApplicationSubmittedEvent cho Job {JobId}", msg.JobId);

        var job = await _jobRepo.GetByIdAsync(msg.JobId);
        if (job != null)
        {
            var frontendUrl = _configuration["FrontendUrl"] ?? "https://jobhub-frontend-two.vercel.app";
            var detailUrl = $"{frontendUrl.TrimEnd('/')}/hr/jobs/{job.Id}/applications";

            await context.Publish(new SendNotificationEvent
            {
                UserId = job.CustomerId,
                Title = "Đơn ứng tuyển mới",
                Message = $"Bạn vừa nhận được hồ sơ ứng tuyển mới cho vị trí: {job.Name}.\n\n👉 [Click vào đây để xem chi tiết]({detailUrl})",
                Type = "invite"
            });
            _logger.LogInformation("Đã publish SendNotificationEvent cho HR {HrId}", job.CustomerId);
        }
        else
        {
            _logger.LogWarning("Không tìm thấy Job với ID {JobId} để gửi thông báo ứng tuyển.", msg.JobId);
        }
    }
}

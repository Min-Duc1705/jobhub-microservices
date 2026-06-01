using CommonService.Events;
using JobService.Repositories.Interface;
using MassTransit;
using Microsoft.Extensions.Logging;
using System.Threading.Tasks;

namespace JobService.Consumers;

public class ApplicationSubmittedConsumer : IConsumer<ApplicationSubmittedEvent>
{
    private readonly IJobRepository _jobRepo;
    private readonly ILogger<ApplicationSubmittedConsumer> _logger;

    public ApplicationSubmittedConsumer(IJobRepository jobRepo, ILogger<ApplicationSubmittedConsumer> _logger)
    {
        _jobRepo = jobRepo;
        this._logger = _logger;
    }

    public async Task Consume(ConsumeContext<ApplicationSubmittedEvent> context)
    {
        var msg = context.Message;
        _logger.LogInformation("JobService nhận được ApplicationSubmittedEvent cho Job {JobId}", msg.JobId);

        var job = await _jobRepo.GetByIdAsync(msg.JobId);
        if (job != null)
        {
            await context.Publish(new SendNotificationEvent
            {
                UserId = job.CustomerId,
                Title = "Đơn ứng tuyển mới",
                Message = $"Bạn vừa nhận được hồ sơ ứng tuyển mới cho vị trí: {job.Name}.",
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

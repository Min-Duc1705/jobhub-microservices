using CommonService.Events;
using JobService.Repositories.Interface;
using MassTransit;
using Microsoft.Extensions.Logging;
using System.Threading.Tasks;

namespace JobService.Consumers;

public class ApplicationStatusChangedConsumer : IConsumer<ApplicationStatusChangedEvent>
{
    private readonly IJobRepository _jobRepo;
    private readonly ILogger<ApplicationStatusChangedConsumer> _logger;

    public ApplicationStatusChangedConsumer(IJobRepository jobRepo, ILogger<ApplicationStatusChangedConsumer> _logger)
    {
        _jobRepo = jobRepo;
        this._logger = _logger;
    }

    public async Task Consume(ConsumeContext<ApplicationStatusChangedEvent> context)
    {
        var msg = context.Message;
        _logger.LogInformation("JobService nhận được ApplicationStatusChangedEvent cho Application {ApplicationId}", msg.ApplicationId);

        var job = await _jobRepo.GetByIdAsync(msg.JobId);
        if (job != null)
        {
            string statusVn = msg.Status switch
            {
                "APPROVED" => "được duyệt",
                "REJECTED" => "từ chối",
                _ => msg.Status.ToLower()
            };

            await context.Publish(new SendNotificationEvent
            {
                UserId = msg.CustomerId, // target candidate
                Title = "Kết quả ứng tuyển",
                Message = $"Hồ sơ ứng tuyển của bạn cho vị trí: {job.Name} tại {job.CompanyName} đã {statusVn}.{(string.IsNullOrEmpty(msg.ReviewNote) ? "" : $" Phản hồi: {msg.ReviewNote}")}",
                Type = "invite"
            });
            _logger.LogInformation("Đã publish SendNotificationEvent cho Candidate {CandidateId}", msg.CustomerId);
        }
        else
        {
            _logger.LogWarning("Không tìm thấy Job với ID {JobId} để gửi thông báo thay đổi trạng thái ứng tuyển.", msg.JobId);
        }
    }
}

using CommonService.Events;
using MassTransit;
using NotificationService.Services.Interface;

namespace NotificationService.Consumers;

public class OtpRequestedConsumer : IConsumer<OtpRequestedEvent>
{
    private readonly IEmailService _emailService;
    private readonly ILogger<OtpRequestedConsumer> _logger;

    public OtpRequestedConsumer(IEmailService emailService, ILogger<OtpRequestedConsumer> logger)
    {
        _emailService = emailService;
        _logger       = logger;
    }

    public async Task Consume(ConsumeContext<OtpRequestedEvent> context)
    {
        var evt = context.Message;

        _logger.LogInformation(
            "Received OtpRequestedEvent: Email={Email}, Type={Type}",
            evt.Email, evt.OtpType);

        try
        {
            await _emailService.SendOtpEmailAsync(evt.Email, evt.OtpCode, evt.OtpType);

            _logger.LogInformation(
                "OTP email sent successfully to {Email}", evt.Email);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex,
                "Failed to send OTP email to {Email}", evt.Email);
            throw; // MassTransit sẽ retry tự động
        }
    }
}

using CommonService.Events;
using MassTransit;
using Microsoft.Extensions.Logging;
using ProfileService.Repositories.Interface;
using System.Threading.Tasks;

namespace ProfileService.Consumers;

public class ProfileUserDeletedConsumer : IConsumer<UserDeletedEvent>
{
    private readonly ICustomerRepository _customerRepository;
    private readonly ILogger<ProfileUserDeletedConsumer> _logger;

    public ProfileUserDeletedConsumer(ICustomerRepository customerRepository, ILogger<ProfileUserDeletedConsumer> logger)
    {
        _customerRepository = customerRepository;
        _logger = logger;
    }

    public async Task Consume(ConsumeContext<UserDeletedEvent> context)
    {
        var message = context.Message;
        _logger.LogInformation("Nhận được sự kiện xóa User từ Auth: {UserId}", message.UserId);

        var customer = await _customerRepository.GetByAppUserIdAsync(message.UserId);
        if (customer == null)
        {
            _logger.LogWarning("Không tìm thấy hồ sơ Customer cho AppUser {UserId}, bỏ qua.", message.UserId);
            return;
        }

        _customerRepository.Delete(customer);
        await _customerRepository.SaveChangesAsync();
        _logger.LogInformation("Đã xóa hồ sơ Customer cho AppUser {UserId}", message.UserId);
    }
}

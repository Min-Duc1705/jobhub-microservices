using CommonService.Events;
using MassTransit;
using ProfileService.Models;
using ProfileService.Models.Enums;
using ProfileService.Repositories.Interface;

namespace ProfileService.Consumers;

public class UserRegisteredEventConsumer : IConsumer<UserRegisteredEvent>
{
    private readonly ICustomerRepository _customerRepository;
    private readonly ILogger<UserRegisteredEventConsumer> _logger;

    public UserRegisteredEventConsumer(ICustomerRepository customerRepository, ILogger<UserRegisteredEventConsumer> logger)
    {
        _customerRepository = customerRepository;
        _logger = logger;
    }

    public async Task Consume(ConsumeContext<UserRegisteredEvent> context)
    {
        var message = context.Message;
        _logger.LogInformation("Nhận được sự kiện đăng ký User từ Auth: {Email}", message.Email);

        // Kiểm tra xem Customer đã tồn tại chưa để tránh tạo trùng (Idempotent)
        var existing = await _customerRepository.GetByAppUserIdAsync(message.UserId);
        if (existing != null)
        {
            _logger.LogWarning("Hồ sơ cho AppUser {UserId} đã tồn tại, bỏ qua.", message.UserId);
            return;
        }

        // Map role đăng ký → CustomerType (dùng dictionary để dễ mở rộng)
        var roleTypeMap = new Dictionary<string, CustomerType>(StringComparer.OrdinalIgnoreCase)
        {
            { "CANDIDATE", CustomerType.CANDIDATE },
            { "HR",        CustomerType.EMPLOYER  },
            { "EMPLOYER",  CustomerType.EMPLOYER  },
            // Thêm role mới ở đây nếu cần
        };

        var customerType = roleTypeMap.TryGetValue(message.Role ?? "", out var mapped)
            ? mapped
            : CustomerType.CANDIDATE;  // fallback an toàn

        var newCustomer = new Customer
        {
            AppUserId   = message.UserId,
            Type        = customerType,
            FullName    = message.Username,   // dùng Username làm tên ban đầu
            CreatedDate = DateTimeOffset.UtcNow,
            CreatedBy   = "System"
        };

        await _customerRepository.AddAsync(newCustomer);
        await _customerRepository.SaveChangesAsync();
        _logger.LogInformation("Đã tự động tạo hồ sơ Customer ({Type}) cho {Email}", customerType, message.Email);
    }
}

using CommonService.Events;
using CommonService.Caching;
using MassTransit;
using ProfileService.Models;
using ProfileService.Repositories.Interface;

namespace ProfileService.Consumers;

public class SkillCreatedConsumer : IConsumer<SkillCreatedEvent>
{
    private readonly ISkillRepository _skillRepository;
    private readonly ICacheService    _cacheService;
    private readonly ILogger<SkillCreatedConsumer> _logger;

    public SkillCreatedConsumer(
        ISkillRepository skillRepository, 
        ICacheService cacheService,
        ILogger<SkillCreatedConsumer> logger)
    {
        _skillRepository = skillRepository;
        _cacheService    = cacheService;
        _logger          = logger;
    }

    public async Task Consume(ConsumeContext<SkillCreatedEvent> context)
    {
        var message = context.Message;
        _logger.LogInformation("Nhận event SkillCreated từ JobService: {Name} (ID: {Id})", message.Name, message.Id);

        // Kiểm tra idempotent
        var existing = await _skillRepository.GetByIdAsync(message.Id);
        if (existing != null)
        {
            _logger.LogWarning("Kỹ năng {Name} (ID: {Id}) đã tồn tại trong replica, bỏ qua.", message.Name, message.Id);
            return;
        }

        var newSkill = new Skill
        {
            Id          = message.Id,
            Name        = message.Name,
            CreatedDate = DateTimeOffset.UtcNow,
            CreatedBy   = "system",
            IsDeleted   = false
        };

        await _skillRepository.AddAsync(newSkill);
        await _skillRepository.SaveChangesAsync();

        await _cacheService.RemoveAsync("profile_skills:dropdown");

        _logger.LogInformation("Đã đồng bộ kỹ năng mới: {Name}", message.Name);
    }
}

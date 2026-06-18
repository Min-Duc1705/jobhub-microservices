using CommonService.Events;
using CommonService.Caching;
using MassTransit;
using ProfileService.Repositories.Interface;

namespace ProfileService.Consumers;

public class SkillDeletedConsumer : IConsumer<SkillDeletedEvent>
{
    private readonly ISkillRepository _skillRepository;
    private readonly ICacheService    _cacheService;
    private readonly ILogger<SkillDeletedConsumer> _logger;

    public SkillDeletedConsumer(
        ISkillRepository skillRepository, 
        ICacheService cacheService,
        ILogger<SkillDeletedConsumer> logger)
    {
        _skillRepository = skillRepository;
        _cacheService    = cacheService;
        _logger          = logger;
    }

    public async Task Consume(ConsumeContext<SkillDeletedEvent> context)
    {
        var message = context.Message;
        _logger.LogInformation("Nhận event SkillDeleted từ JobService cho ID: {Id}", message.Id);

        var skill = await _skillRepository.GetByIdAsync(message.Id);
        if (skill == null)
        {
            _logger.LogWarning("Không tìm thấy kỹ năng ID: {Id} trong replica để xóa.", message.Id);
            return;
        }

        // Soft delete replica
        skill.IsDeleted        = true;
        skill.LastModifiedDate = DateTimeOffset.UtcNow;
        skill.LastModifiedBy   = "system";
        
        _skillRepository.Update(skill);
        await _skillRepository.SaveChangesAsync();

        await _cacheService.RemoveAsync("profile_skills:dropdown");

        _logger.LogInformation("Đã đồng bộ xóa kỹ năng ID: {Id}", message.Id);
    }
}

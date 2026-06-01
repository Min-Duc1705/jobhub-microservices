using CommonService.Events;
using MassTransit;
using ProfileService.Repositories.Interface;

namespace ProfileService.Consumers;

public class SkillUpdatedConsumer : IConsumer<SkillUpdatedEvent>
{
    private readonly ISkillRepository _skillRepository;
    private readonly ILogger<SkillUpdatedConsumer> _logger;

    public SkillUpdatedConsumer(ISkillRepository skillRepository, ILogger<SkillUpdatedConsumer> logger)
    {
        _skillRepository = skillRepository;
        _logger          = logger;
    }

    public async Task Consume(ConsumeContext<SkillUpdatedEvent> context)
    {
        var message = context.Message;
        _logger.LogInformation("Nhận event SkillUpdated từ JobService: {Name} (ID: {Id})", message.Name, message.Id);

        var skill = await _skillRepository.GetByIdAsync(message.Id);
        if (skill == null)
        {
            _logger.LogWarning("Không tìm thấy kỹ năng ID: {Id} trong replica để cập nhật. Đang tiến hành tạo mới...", message.Id);
            var newSkill = new ProfileService.Models.Skill
            {
                Id          = message.Id,
                Name        = message.Name,
                CreatedDate = DateTimeOffset.UtcNow,
                CreatedBy   = "system",
                IsDeleted   = false
            };
            await _skillRepository.AddAsync(newSkill);
        }
        else
        {
            skill.Name             = message.Name;
            skill.LastModifiedDate = DateTimeOffset.UtcNow;
            skill.LastModifiedBy   = "system";
            _skillRepository.Update(skill);
        }

        await _skillRepository.SaveChangesAsync();
        _logger.LogInformation("Đã đồng bộ cập nhật kỹ năng: {Name}", message.Name);
    }
}

using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using ProfileService.Models;
using ProfileService.Models.Request;
using ProfileService.Models.Response;
using ProfileService.Repositories.Interface;
using ProfileService.Services.Interface;
using ProfileService.Specifications;
using CommonService.Caching;

namespace ProfileService.Services;

public class SkillServiceImpl : ISkillService
{
    private readonly ISkillRepository    _skillRepo;
    private readonly ICustomerRepository _customerRepo;
    private readonly IMapper             _mapper;
    private readonly ICacheService       _cacheService;
    private const string CACHE_KEY_DROPDOWN = "profile_skills:dropdown";

    public SkillServiceImpl(
        ISkillRepository skillRepo, 
        ICustomerRepository customerRepo, 
        IMapper mapper,
        ICacheService cacheService)
    {
        _skillRepo    = skillRepo;
        _customerRepo = customerRepo;
        _mapper       = mapper;
        _cacheService = cacheService;
    }

    public async Task<ResultPaginationDto<SkillResponse>> GetAllAsync(SkillFilterRequest filter)
    {
        var spec      = new SkillFilterSpec(filter.SearchTerm, filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);
        var countSpec = new SkillFilterCountSpec(filter.SearchTerm);

        var items      = await _skillRepo.ListAsync(spec);
        var totalCount = await _skillRepo.CountAsync(countSpec);

        return new ResultPaginationDto<SkillResponse>(
            _mapper.Map<List<SkillResponse>>(items),
            filter.PageNumber, filter.PageSize, (int)totalCount);
    }

    public async Task<List<SkillResponse>> GetDropdownAsync()
    {
        var cached = await _cacheService.GetAsync<List<SkillResponse>>(CACHE_KEY_DROPDOWN);
        if (cached != null) return cached;

        // GetAllAsync() của GenericRepository đã lọc IsDeleted = false rồi
        var skills = await _skillRepo.GetAllAsync();
        var response = _mapper.Map<List<SkillResponse>>(skills);

        await _cacheService.SetAsync(CACHE_KEY_DROPDOWN, response, TimeSpan.FromHours(4));
        return response;
    }

    public async Task<SkillResponse> GetByIdAsync(Guid id)
    {
        var skill = await _skillRepo.GetByIdAsync(id);
        if (skill == null || skill.IsDeleted)
            throw new NotFoundException($"Không tìm thấy Skill với ID: {id}");

        return _mapper.Map<SkillResponse>(skill);
    }

    public async Task<SkillResponse> CreateAsync(CreateSkillRequest request)
    {
        var existing = await _skillRepo.GetByNameAsync(request.Name);
        if (existing != null)
            throw new BadRequestException($"Skill '{request.Name}' đã tồn tại.");

        var skill = new Skill
        {
            Name          = request.Name,
            CreatedDate   = DateTimeOffset.UtcNow,
            CreatedBy     = "System"
        };
        await _skillRepo.AddAsync(skill);
        await _skillRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);

        return _mapper.Map<SkillResponse>(skill);
    }

    public async Task<SkillResponse> UpdateAsync(Guid id, UpdateSkillRequest request)
    {
        var skill = await _skillRepo.GetByIdAsync(id);
        if (skill == null || skill.IsDeleted)
            throw new NotFoundException($"Không tìm thấy Skill với ID: {id}");

        var conflict = await _skillRepo.GetByNameAsync(request.Name);
        if (conflict != null && conflict.Id != id)
            throw new BadRequestException($"Skill '{request.Name}' đã tồn tại.");

        skill.Name             = request.Name;
        skill.LastModifiedDate = DateTimeOffset.UtcNow;

        _skillRepo.Update(skill);
        await _skillRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);

        return _mapper.Map<SkillResponse>(skill);
    }

    public async Task DeleteAsync(Guid id)
    {
        var skill = await _skillRepo.GetByIdAsync(id);
        if (skill == null || skill.IsDeleted)
            throw new NotFoundException($"Không tìm thấy Skill với ID: {id}");

        // Soft delete — GenericRepository.Delete() đánh dấu IsDeleted = true
        _skillRepo.Delete(skill);
        await _skillRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);
    }

    // ── Quản lý kỹ năng của Customer ────────────────────────────────────────

    public async Task<CustomerResponse> AddSkillToCustomerAsync(Guid appUserId, AddCustomerSkillRequest request)
    {
        var customer = await _customerRepo.GetByAppUserIdAsync(appUserId)
            ?? throw new NotFoundException("Không tìm thấy hồ sơ cá nhân.");

        var skill = await _skillRepo.GetByIdAsync(request.SkillId);
        if (skill == null || skill.IsDeleted)
            throw new NotFoundException($"Không tìm thấy Skill với ID: {request.SkillId}");

        if (customer.CustomerSkills.Any(cs => cs.SkillId == request.SkillId))
            throw new BadRequestException($"Kỹ năng '{skill.Name}' đã có trong hồ sơ.");

        customer.CustomerSkills.Add(new CustomerSkill
        {
            CustomerId        = customer.Id,
            SkillId           = request.SkillId,
            YearsOfExperience = request.YearsOfExperience
        });

        _customerRepo.Update(customer);
        await _customerRepo.SaveChangesAsync();

        return _mapper.Map<CustomerResponse>(customer);
    }

    public async Task<CustomerResponse> RemoveSkillFromCustomerAsync(Guid appUserId, Guid skillId)
    {
        var customer = await _customerRepo.GetByAppUserIdAsync(appUserId)
            ?? throw new NotFoundException("Không tìm thấy hồ sơ cá nhân.");

        var customerSkill = customer.CustomerSkills.FirstOrDefault(cs => cs.SkillId == skillId)
            ?? throw new NotFoundException("Kỹ năng không tồn tại trong hồ sơ.");

        customer.CustomerSkills.Remove(customerSkill);
        _customerRepo.Update(customer);
        await _customerRepo.SaveChangesAsync();

        return _mapper.Map<CustomerResponse>(customer);
    }
}

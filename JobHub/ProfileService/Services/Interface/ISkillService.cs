using CommonService.Common;
using ProfileService.Models.Request;
using ProfileService.Models.Response;

namespace ProfileService.Services.Interface;

public interface ISkillService
{
    Task<ResultPaginationDto<SkillResponse>> GetAllAsync(SkillFilterRequest filter);
    Task<List<SkillResponse>>               GetDropdownAsync();
    Task<SkillResponse>                     GetByIdAsync(Guid id);
    Task<SkillResponse>                     CreateAsync(CreateSkillRequest request);
    Task<SkillResponse>                     UpdateAsync(Guid id, UpdateSkillRequest request);
    Task                                    DeleteAsync(Guid id);

    // Quản lý kỹ năng của Customer
    Task<CustomerResponse>                  AddSkillToCustomerAsync(Guid appUserId, AddCustomerSkillRequest request);
    Task<CustomerResponse>                  RemoveSkillFromCustomerAsync(Guid appUserId, Guid skillId);
}

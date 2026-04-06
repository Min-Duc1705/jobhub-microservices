using CommonService.Common;
using ProfileService.Models.Request;
using ProfileService.Models.Response;

namespace ProfileService.Services.Interface;

public interface ICustomerService
{
    Task<ResultPaginationDto<CustomerResponse>> GetAllAsync(CustomerFilterRequest filter);
    Task<CustomerResponse>                      GetMyProfileAsync(Guid appUserId);
    Task<CustomerResponse>                      UpdateMyProfileAsync(Guid appUserId, UpdateCustomerRequest request);
    Task<CustomerResponse>                      GetProfileByIdAsync(Guid customerId);
}

using CommonService.Repository;
using ProfileService.Models;

namespace ProfileService.Repositories.Interface;

public interface ICustomerRepository : IGenericRepository<Customer>
{
    Task<Customer?> GetByAppUserIdAsync(Guid appUserId);
}

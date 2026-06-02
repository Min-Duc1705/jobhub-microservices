using CommonService.Repository;
using NotificationService.Models;
using CommonService.Common;
using System.Threading.Tasks;

namespace NotificationService.Repositories.Interface;

public interface IContactRepository : IGenericRepository<Contact>
{
    Task<ResultPaginationDto<Contact>> GetContactsAsync(
        string? searchTerm,
        string? topic,
        int page,
        int pageSize);
}

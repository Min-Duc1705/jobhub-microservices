using System.Threading.Tasks;
using NotificationService.Models;
using NotificationService.Models.Request;
using CommonService.Common;

namespace NotificationService.Services.Interface;

public interface IContactService
{
    Task<Contact> CreateContactAsync(CreateContactRequest request);
    Task<ResultPaginationDto<Contact>> GetContactsAsync(
        string? searchTerm,
        string? topic,
        int page,
        int pageSize);
}

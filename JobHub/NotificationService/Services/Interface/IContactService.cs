using System.Threading.Tasks;
using NotificationService.Models;
using NotificationService.Models.Request;

namespace NotificationService.Services.Interface;

public interface IContactService
{
    Task<Contact> CreateContactAsync(CreateContactRequest request);
}

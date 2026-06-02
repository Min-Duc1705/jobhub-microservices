using CommonService.Repository;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Repositories.Interface;

namespace NotificationService.Repositories;

public class ContactRepository : GenericRepository<NotificationDbContext, Contact>, IContactRepository
{
    public ContactRepository(NotificationDbContext dbContext) : base(dbContext)
    {
    }
}

using CommonService.Exceptions;
using NotificationService.Models;
using NotificationService.Models.Request;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Interface;
using System;
using System.Threading.Tasks;

namespace NotificationService.Services;

public class ContactServiceImpl : IContactService
{
    private readonly IContactRepository _contactRepo;

    public ContactServiceImpl(IContactRepository contactRepo)
    {
        _contactRepo = contactRepo;
    }

    public async Task<Contact> CreateContactAsync(CreateContactRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.FullName) ||
            string.IsNullOrWhiteSpace(request.Email) ||
            string.IsNullOrWhiteSpace(request.Topic) ||
            string.IsNullOrWhiteSpace(request.Message))
        {
            throw new BadRequestException("Vui lòng điền đầy đủ các thông tin bắt buộc.");
        }

        var contact = new Contact
        {
            Id = Guid.NewGuid(),
            FullName = request.FullName.Trim(),
            Email = request.Email.Trim(),
            Phone = request.Phone?.Trim(),
            Topic = request.Topic.Trim(),
            Message = request.Message.Trim(),
            CreatedAt = DateTimeOffset.UtcNow
        };

        await _contactRepo.AddAsync(contact);
        await _contactRepo.SaveChangesAsync();

        return contact;
    }
}

using CommonService.Annotations;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NotificationService.Models.Request;
using NotificationService.Services.Interface;
using System.Threading.Tasks;

namespace NotificationService.Controllers;

[ApiController]
[Route("api/v1/contacts")]
public class ContactsController : ControllerBase
{
    private readonly IContactService _contactService;

    public ContactsController(IContactService contactService)
    {
        _contactService = contactService;
    }

    [HttpPost]
    [AllowAnonymous]
    [ApiMessage("Gửi liên hệ thành công")]
    public async Task<IActionResult> CreateContact([FromBody] CreateContactRequest request)
    {
        var contact = await _contactService.CreateContactAsync(request);
        return Ok(new { id = contact.Id });
    }

    [HttpGet]
    [Authorize]
    [ApiMessage("Lấy danh sách liên hệ thành công")]
    public async Task<IActionResult> GetContacts(
        [FromQuery] string? searchTerm,
        [FromQuery] string? topic,
        [FromQuery] int pageNumber = 1,
        [FromQuery] int pageSize = 10)
    {
        var result = await _contactService.GetContactsAsync(searchTerm, topic, pageNumber, pageSize);
        return Ok(result);
    }
}

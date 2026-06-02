using AutoMapper;
using NotificationService.Models;
using NotificationService.Models.Response;

namespace NotificationService.Mapping;

public class NotificationMappingProfile : Profile
{
    public NotificationMappingProfile()
    {
        CreateMap<Notification, NotificationResponse>();
        CreateMap<Conversation, ConversationResponse>();
        CreateMap<Message, MessageResponse>();
    }
}

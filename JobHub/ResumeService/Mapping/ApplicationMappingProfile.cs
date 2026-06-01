using AutoMapper;
using ResumeService.Models;
using ResumeService.Models.Request;
using ResumeService.Models.Response;

namespace ResumeService.Mapping;

public class ApplicationMappingProfile : Profile
{
    public ApplicationMappingProfile()
    {
        CreateMap<Application, ApplicationResponse>()
            .ForMember(dest => dest.Resume,
                opt => opt.MapFrom(src => src.Resume));

        CreateMap<CreateApplicationRequest, Application>();
    }
}

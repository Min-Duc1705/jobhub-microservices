using AutoMapper;
using ResumeService.Models;
using ResumeService.Models.Request;
using ResumeService.Models.Response;

namespace ResumeService.Mapping;

public class ResumeMappingProfile : Profile
{
    public ResumeMappingProfile()
    {
        CreateMap<Resume, ResumeResponse>();

        CreateMap<CreateResumeRequest, Resume>();

        CreateMap<UpdateResumeRequest, Resume>()
            .ForAllMembers(opt => opt.Condition((src, dest, srcMember) => srcMember != null));
    }
}

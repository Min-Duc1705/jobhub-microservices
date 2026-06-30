using AutoMapper;
using ResumeService.Models;
using ResumeService.Models.Request;
using ResumeService.Models.Response;

namespace ResumeService.Mapping;

public class InterviewMappingProfile : Profile
{
    public InterviewMappingProfile()
    {
        CreateMap<Interview, InterviewResponse>();
        CreateMap<CreateInterviewRequest, Interview>();
        CreateMap<UpdateInterviewRequest, Interview>();
    }
}

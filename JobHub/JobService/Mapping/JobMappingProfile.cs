using AutoMapper;
using JobService.Models;
using JobService.Models.Request;
using JobService.Models.Response;

namespace JobService.Mapping;

public class JobMappingProfile : Profile
{
    public JobMappingProfile()
    {
        // ── Job ───────────────────────────────────────────────────────────────
        CreateMap<Job, JobResponse>()
            .ForMember(dest => dest.Skills,
                opt => opt.MapFrom(src => src.JobSkills.Where(js => js.Skill != null).Select(js => js.Skill)));

        CreateMap<CreateJobRequest, Job>()
            .ForMember(dest => dest.JobSkills, opt => opt.Ignore()); // JobSkills được xử lý thủ công

        CreateMap<UpdateJobRequest, Job>()
            .ForMember(dest => dest.JobSkills, opt => opt.Ignore())
            .ForAllMembers(opt => opt.Condition((src, dest, srcMember) => srcMember != null));

        // ── Skill ─────────────────────────────────────────────────────────────
        CreateMap<Skill, SkillResponse>();
        CreateMap<Skill, SkillDto>();
        CreateMap<CreateSkillRequest, Skill>();

        // ── SavedJob ──────────────────────────────────────────────────────────
        CreateMap<SavedJob, SavedJobResponse>()
            .ForMember(dest => dest.Job, opt => opt.MapFrom(src => src.Job));
    }
}

using AutoMapper;
using ProfileService.Models;
using ProfileService.Models.Request;
using ProfileService.Models.Response;

namespace ProfileService.Mapping;

public class ProfileMappingProfile : Profile
{
    public ProfileMappingProfile()
    {
        CreateMap<Customer, CustomerResponse>()
            .ForMember(dest => dest.Skills, opt => opt.MapFrom(src => src.CustomerSkills));

        CreateMap<CustomerSkill, CustomerSkillDto>()
            .ForMember(dest => dest.SkillName, opt => opt.MapFrom(src => src.Skill.Name));

        CreateMap<UpdateCustomerRequest, Customer>()
            .ForAllMembers(opts => opts.Condition((src, dest, srcMember) => srcMember != null));

        CreateMap<Skill, SkillResponse>();
    }
}

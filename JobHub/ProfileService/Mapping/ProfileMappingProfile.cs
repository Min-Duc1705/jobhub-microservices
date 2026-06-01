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
            // PostgreSQL 'timestamp with time zone' yêu cầu Kind=Utc.
            // DateTime từ JSON body có Kind=Unspecified → cần SpecifyKind(Utc) trước khi lưu.
            .ForMember(dest => dest.DateOfBirth, opt => opt.MapFrom(
                src => src.DateOfBirth.HasValue
                    ? DateTime.SpecifyKind(src.DateOfBirth.Value, DateTimeKind.Utc)
                    : (DateTime?)null))
            // Guid? (nullable value type) không tương thích tốt với ForAllMembers null-check
            // → Khai báo tường minh để đảm bảo luôn được map khi Employer cập nhật công ty.
            .ForMember(dest => dest.CompanyId, opt => opt.MapFrom(src => src.CompanyId))
            .ForMember(dest => dest.Position,   opt => opt.MapFrom(src => src.Position))
            .ForAllMembers(opts => opts.Condition((src, dest, srcMember) => srcMember != null));

        CreateMap<Skill, SkillResponse>();
    }
}

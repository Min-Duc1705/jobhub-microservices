using AutoMapper;
using CompanyService.Models;
using CompanyService.Models.Request;
using CompanyService.Models.Response;

namespace CompanyService.Mapping;

public class CompanyMappingProfile : Profile
{
    public CompanyMappingProfile()
    {
        // Entity → Response DTO
        CreateMap<Company, CompanyResponse>();

        // CreateRequest → Entity (dùng khi tạo mới)
        CreateMap<CreateCompanyRequest, Company>();

        // UpdateRequest → Entity (chỉ map những field không null)
        CreateMap<UpdateCompanyRequest, Company>()
            .ForAllMembers(opts => opts.Condition((src, dest, srcMember) => srcMember != null));
    }
}

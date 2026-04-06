using AuthService.Models;
using AuthService.Models.Response;
using AutoMapper;

namespace AuthService.Mapping;

public class AuthMappingProfile : Profile
{
    public AuthMappingProfile()
    {
        // ── Permission ────────────────────────────────────────────────────────
        CreateMap<Permission, PermissionResponse>();

        // Nested dùng trong LoginResponse
        CreateMap<Permission, UserLoginDto.PermissionDto>();

        // ── Role ──────────────────────────────────────────────────────────────
        CreateMap<Role, RoleResponse>()
            .ForMember(dest => dest.IsActive,    opt => opt.MapFrom(src => src.Active))
            .ForMember(dest => dest.UserCount,   opt => opt.MapFrom(src => src.Users != null ? src.Users.Count : 0))
            .ForMember(dest => dest.Permissions, opt => opt.MapFrom(src => src.Permissions));

        // Nested dùng trong LoginResponse
        CreateMap<Role, UserLoginDto.RoleDto>()
            .ForMember(dest => dest.Permissions, opt => opt.MapFrom(src => src.Permissions));

        // Dropdown
        CreateMap<Role, RoleDropdownDto>();

        // ── AppUser ───────────────────────────────────────────────────────────
        CreateMap<AppUser, UserResponse>()
            .ForMember(dest => dest.Username, opt => opt.MapFrom(src => src.Email))
            .ForMember(dest => dest.Status,   opt => opt.MapFrom(src => src.Status.ToString()))
            .ForMember(dest => dest.Role,     opt => opt.MapFrom(src => src.Role));

        // Nested Role trong UserResponse
        CreateMap<Role, UserResponse.RoleDto>();

        // Nested dùng trong LoginResponse
        CreateMap<AppUser, UserLoginDto>()
            .ForMember(dest => dest.Username, opt => opt.MapFrom(src => src.Email))
            .ForMember(dest => dest.Status,   opt => opt.MapFrom(src => src.Status.ToString()))
            .ForMember(dest => dest.Role,     opt => opt.MapFrom(src => src.Role));

        // ── Register Response ─────────────────────────────────────────────────
        CreateMap<AppUser, RegisterResponseDTO>()
            .ForMember(dest => dest.Username, opt => opt.Ignore()); // username set từ request
    }
}

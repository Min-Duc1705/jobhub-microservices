using AuthService.Models;
using AuthService.Models.Request;
using AuthService.Models.Response;
using AuthService.Repositories.Interface;
using AuthService.Services.Interface;
using AuthService.Specifications;
using AutoMapper;
using CommonService.Caching;
using CommonService.Common;
using CommonService.Exceptions;

namespace AuthService.Services;

public class RoleServiceImpl : IRoleService
{
    private readonly IRoleRepository       _roleRepo;
    private readonly IPermissionRepository _permissionRepo;
    private readonly ICacheService         _cacheService;
    private readonly IMapper               _mapper;
    private const string CACHE_KEY_DROPDOWN = "roles:dropdown";

    public RoleServiceImpl(
        IRoleRepository       roleRepo,
        IPermissionRepository permissionRepo,
        ICacheService         cacheService,
        IMapper               mapper)
    {
        _roleRepo       = roleRepo;
        _permissionRepo = permissionRepo;
        _cacheService   = cacheService;
        _mapper         = mapper;
    }

    public async Task<ResultPaginationDto<RoleResponse>> GetAllRolesAsync(RoleFilterRequest filter)
    {
        var spec      = new RoleFilterSpec(filter.SearchTerm, filter.IsActive, filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);
        var countSpec = new RoleFilterCountSpec(filter.SearchTerm, filter.IsActive);

        var roles      = await _roleRepo.ListAsync(spec);
        var totalCount = await _roleRepo.CountAsync(countSpec);

        return new ResultPaginationDto<RoleResponse>(
            _mapper.Map<List<RoleResponse>>(roles),
            filter.PageNumber, filter.PageSize, (int)totalCount);
    }

    public async Task<RoleResponse> GetRoleByIdAsync(Guid id)
    {
        var role = await _roleRepo.GetEntityWithSpec(new RoleByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy Role với ID: {id}");

        return _mapper.Map<RoleResponse>(role);
    }

    public async Task<RoleResponse> CreateRoleAsync(CreateRoleRequest request)
    {
        var existing = await _roleRepo.GetByNameAsync(request.Name);
        if (existing != null)
            throw new BadRequestException($"Role '{request.Name}' đã tồn tại.");

        var permissions = new List<Permission>();
        foreach (var pid in request.PermissionIds)
        {
            var p = await _permissionRepo.GetEntityWithSpec(new PermissionByIdSpec(pid))
                ?? throw new BadRequestException($"Permission ID {pid} không tồn tại.");
            permissions.Add(p);
        }

        var role = new Role
        {
            Name        = request.Name,
            Description = request.Description,
            Active      = true,
            CreatedDate = DateTimeOffset.UtcNow,
            Permissions = permissions,
        };

        await _roleRepo.AddAsync(role);
        await _roleRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);

        return _mapper.Map<RoleResponse>(role);
    }

    public async Task<RoleResponse> UpdateRoleAsync(Guid id, UpdateRoleRequest request)
    {
        var role = await _roleRepo.GetWithPermissionsAsync(id)
            ?? throw new NotFoundException($"Không tìm thấy Role với ID: {id}");

        var sameNameRole = await _roleRepo.GetByNameAsync(request.Name);
        if (sameNameRole != null && sameNameRole.Id != id)
            throw new BadRequestException($"Role '{request.Name}' đã tồn tại.");

        role.Name             = request.Name;
        role.Description      = request.Description;
        role.Active           = request.IsActive;
        role.LastModifiedDate = DateTimeOffset.UtcNow;

        if (request.PermissionIds != null)
        {
            if (!request.PermissionIds.Any())
                throw new BadRequestException("Phải có ít nhất 1 Permission.");

            var newIds     = request.PermissionIds.ToHashSet();
            var currentIds = role.Permissions.Select(p => p.Id).ToHashSet();

            var toRemove = role.Permissions.Where(p => !newIds.Contains(p.Id)).ToList();
            foreach (var p in toRemove) role.Permissions.Remove(p);

            var toAddIds = newIds.Where(pid => !currentIds.Contains(pid)).ToList();
            if (toAddIds.Any())
            {
                var toAdd = await _permissionRepo.GetPermissionsByIdsAsync(toAddIds);
                if (toAdd.Count != toAddIds.Count)
                    throw new BadRequestException("Một hoặc nhiều Permission ID không tồn tại.");
                foreach (var p in toAdd) role.Permissions.Add(p);
            }
        }

        _roleRepo.Update(role);
        await _roleRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);
        await InvalidatePermissionCacheForRoleAsync(id);

        return _mapper.Map<RoleResponse>(role);
    }

    public async Task DeleteRoleAsync(Guid id)
    {
        var spec = new RoleByIdSpec(id);
        var role = await _roleRepo.GetEntityWithSpec(spec)
            ?? throw new NotFoundException($"Không tìm thấy Role với ID: {id}");

        if (role.Users.Any())
            throw new BadRequestException(
                $"Không thể xóa Role '{role.Name}' vì có {role.Users.Count} user đang sử dụng.");

        _roleRepo.Delete(role);
        await _roleRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);
    }

    public async Task<List<RoleDropdownDto>> GetDropdownAsync()
    {
        var cached = await _cacheService.GetAsync<List<RoleDropdownDto>>(CACHE_KEY_DROPDOWN);
        if (cached != null) return cached;

        var roles    = await _roleRepo.GetAllDropdownAsync();
        var response = _mapper.Map<List<RoleDropdownDto>>(roles);

        await _cacheService.SetAsync(CACHE_KEY_DROPDOWN, response, TimeSpan.FromDays(7));

        return response;
    }

    private async Task InvalidatePermissionCacheForRoleAsync(Guid roleId)
    {
        var emails = await _roleRepo.GetUserEmailsByRoleIdAsync(roleId);
        if (emails.Count == 0) return;
        var deleteTasks = emails.Select(email => _cacheService.RemoveAsync($"perm:{email}"));
        await Task.WhenAll(deleteTasks);
    }
}

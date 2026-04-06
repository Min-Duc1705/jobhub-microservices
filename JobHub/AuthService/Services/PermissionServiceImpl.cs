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

public class PermissionServiceImpl : IPermissionService
{
    private readonly IPermissionRepository _permissionRepo;
    private readonly ICacheService         _cacheService;
    private readonly IMapper               _mapper;
    private const string CACHE_KEY_DROPDOWN = "permissions:dropdown";

    public PermissionServiceImpl(IPermissionRepository permissionRepo, ICacheService cacheService, IMapper mapper)
    {
        _permissionRepo = permissionRepo;
        _cacheService   = cacheService;
        _mapper         = mapper;
    }

    public async Task<ResultPaginationDto<PermissionResponse>> GetAllPermissionsAsync(PermissionFilterRequest filter)
    {
        var spec      = new PermissionFilterSpec(filter.SearchTerm, filter.Module, filter.Method, filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);
        var countSpec = new PermissionFilterCountSpec(filter.SearchTerm, filter.Module, filter.Method);

        var items      = await _permissionRepo.ListAsync(spec);
        var totalCount = await _permissionRepo.CountAsync(countSpec);

        return new ResultPaginationDto<PermissionResponse>(
            _mapper.Map<List<PermissionResponse>>(items),
            filter.PageNumber, filter.PageSize, (int)totalCount);
    }

    public async Task<PermissionResponse> GetPermissionByIdAsync(Guid id)
    {
        var perm = await _permissionRepo.GetEntityWithSpec(new PermissionByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy Permission với ID: {id}");

        return _mapper.Map<PermissionResponse>(perm);
    }

    public async Task<PermissionResponse> CreatePermissionAsync(CreatePermissionRequest request)
    {
        var existing = await _permissionRepo.GetByPathAndMethodAsync(request.ApiPath, request.Method);
        if (existing != null)
            throw new BadRequestException($"Permission '{request.Method} {request.ApiPath}' đã tồn tại.");

        var permission = new Permission
        {
            Name        = request.Name,
            ApiPath     = request.ApiPath,
            Method      = request.Method.ToUpper(),
            Module      = request.Module,
            CreatedDate = DateTimeOffset.UtcNow,
        };

        await _permissionRepo.AddAsync(permission);
        await _permissionRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);

        return _mapper.Map<PermissionResponse>(permission);
    }

    public async Task<PermissionResponse> UpdatePermissionAsync(Guid id, UpdatePermissionRequest request)
    {
        var perm = await _permissionRepo.GetEntityWithSpec(new PermissionByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy Permission với ID: {id}");

        var conflict = await _permissionRepo.GetByPathAndMethodAsync(request.ApiPath, request.Method);
        if (conflict != null && conflict.Id != id)
            throw new BadRequestException($"Permission '{request.Method} {request.ApiPath}' đã tồn tại.");

        perm.Name             = request.Name;
        perm.ApiPath          = request.ApiPath;
        perm.Method           = request.Method.ToUpper();
        perm.Module           = request.Module;
        perm.LastModifiedDate = DateTimeOffset.UtcNow;

        _permissionRepo.Update(perm);
        await _permissionRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);

        return _mapper.Map<PermissionResponse>(perm);
    }

    public async Task DeletePermissionAsync(Guid id)
    {
        var perm = await _permissionRepo.GetEntityWithSpec(new PermissionByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy Permission với ID: {id}");

        _permissionRepo.Delete(perm);
        await _permissionRepo.SaveChangesAsync();

        await _cacheService.RemoveAsync(CACHE_KEY_DROPDOWN);
    }

    public async Task<List<PermissionResponse>> GetDropdownAsync()
    {
        var cached = await _cacheService.GetAsync<List<PermissionResponse>>(CACHE_KEY_DROPDOWN);
        if (cached != null) return cached;

        var permissions = await _permissionRepo.GetAllDropdownAsync();
        var response    = _mapper.Map<List<PermissionResponse>>(permissions);

        await _cacheService.SetAsync(CACHE_KEY_DROPDOWN, response, TimeSpan.FromDays(7));

        return response;
    }
}

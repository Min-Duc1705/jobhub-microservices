using AuthService.Models;
using AuthService.Models.Request;
using AuthService.Models.Response;
using AuthService.Repositories.Interface;
using AuthService.Services.Interface;
using AuthService.Specifications;
using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using CommonService.Events;
using MassTransit;

namespace AuthService.Services;

public class UserServiceImpl : IUserService
{
    private readonly IAppUserRepository _userRepo;
    private readonly IRoleRepository    _roleRepo;
    private readonly IMapper            _mapper;
    private readonly IPublishEndpoint   _publishEndpoint;

    public UserServiceImpl(IAppUserRepository userRepo, IRoleRepository roleRepo, IMapper mapper, IPublishEndpoint publishEndpoint)
    {
        _userRepo = userRepo;
        _roleRepo = roleRepo;
        _mapper   = mapper;
        _publishEndpoint = publishEndpoint;
    }

    public async Task<ResultPaginationDto<UserResponse>> GetAllUsersAsync(UserFilterRequest filter)
    {
        var spec      = new UserFilterSpec(
            filter.SearchTerm, filter.Status, filter.RoleId,
            filter.SortBy, filter.IsDescending,
            filter.PageNumber, filter.PageSize);
        var countSpec = new UserFilterCountSpec(filter.SearchTerm, filter.Status, filter.RoleId);

        var users      = await _userRepo.ListAsync(spec);
        var totalCount = await _userRepo.CountAsync(countSpec);

        return new ResultPaginationDto<UserResponse>(
            _mapper.Map<List<UserResponse>>(users),
            filter.PageNumber, filter.PageSize, (int)totalCount);
    }

    public async Task<UserResponse> GetUserByIdAsync(Guid id)
    {
        var user = await _userRepo.GetEntityWithSpec(new UserByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy user với ID: {id}");

        return _mapper.Map<UserResponse>(user);
    }

    public async Task<UserResponse> CreateUserAsync(CreateUserRequest request)
    {
        if (await _userRepo.EmailExistsAsync(request.Email))
            throw new BadRequestException($"Email '{request.Email}' đã tồn tại.");

        if (request.RoleId.HasValue)
        {
            var roleExists = await _roleRepo.GetEntityWithSpec(new RoleByIdSpec(request.RoleId.Value));
            if (roleExists is null)
                throw new BadRequestException($"Role ID '{request.RoleId}' không tồn tại.");
        }

        var user = new AppUser
        {
            Email        = request.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
            Status       = UserStatus.Active,
            RoleId       = request.RoleId ?? Guid.Empty,
            CreatedDate  = DateTimeOffset.UtcNow,
        };

        await _userRepo.AddAsync(user);
        await _userRepo.SaveChangesAsync();

        return await GetUserByIdAsync(user.Id);
    }

    public async Task<UserResponse> UpdateUserAsync(Guid id, UpdateUserRequest request)
    {
        var user = await _userRepo.GetEntityWithSpec(new UserByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy user với ID: {id}");

        if (!user.Email.Equals(request.Email, StringComparison.OrdinalIgnoreCase)
            && await _userRepo.EmailExistsAsync(request.Email))
            throw new BadRequestException($"Email '{request.Email}' đã được sử dụng.");

        if (request.RoleId.HasValue)
        {
            var roleExists = await _roleRepo.GetEntityWithSpec(new RoleByIdSpec(request.RoleId.Value));
            if (roleExists is null)
                throw new BadRequestException($"Role ID '{request.RoleId}' không tồn tại.");
        }

        if (Enum.TryParse<UserStatus>(request.Status, out var newStatus))
            user.Status = newStatus;

        user.Username         = request.Username;
        user.Email            = request.Email;
        user.RoleId           = request.RoleId ?? user.RoleId;
        user.LastModifiedDate = DateTimeOffset.UtcNow;

        _userRepo.Update(user);
        await _userRepo.SaveChangesAsync();

        return _mapper.Map<UserResponse>(user);
    }

    public async Task DeleteUserAsync(Guid id)
    {
        var user = await _userRepo.GetEntityWithSpec(new UserByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy user với ID: {id}");

        _userRepo.Delete(user);
        await _userRepo.SaveChangesAsync();
    }

    public async Task BroadcastNotificationAsync(BroadcastNotificationRequest request)
    {
        var users = await _userRepo.GetUsersByRoleAsync(request.TargetGroup);
        foreach (var user in users)
        {
            await _publishEndpoint.Publish(new SendNotificationEvent
            {
                UserId = user.Id,
                Title = request.Title,
                Message = request.Message,
                Type = request.Type
            });
        }
        await _userRepo.SaveChangesAsync();
    }

    public async Task ResetPasswordAsync(Guid id, ResetPasswordRequest request)
    {
        var user = await _userRepo.GetEntityWithSpec(new UserByIdSpec(id))
            ?? throw new NotFoundException($"Không tìm thấy user với ID: {id}");

        user.PasswordHash     = BCrypt.Net.BCrypt.HashPassword(request.NewPassword);
        user.LastModifiedDate = DateTimeOffset.UtcNow;

        _userRepo.Update(user);
        await _userRepo.SaveChangesAsync();
    }
}

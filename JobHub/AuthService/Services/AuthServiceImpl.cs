 using AuthService.Models;
using AuthService.Models.Request;
using AuthService.Models.Response;
using AuthService.Repositories.Interface;
using AuthService.Services.Interface;
using AutoMapper;
using CommonService.Caching;
using CommonService.Events;
using CommonService.Exceptions;
using CommonService.Models;
using MassTransit;


namespace AuthService.Services
{
    public class AuthServiceImpl : IAuthService
    {
        private readonly IAppUserRepository      _userRepo;
        private readonly IRoleRepository         _roleRepo;
        private readonly ITokenService           _tokenService;
        private readonly IConfiguration          _configuration;
        private readonly IHttpContextAccessor    _httpContextAccessor;
        private readonly IPublishEndpoint        _publishEndpoint;
        private readonly ICacheService           _cache;
        private readonly IMapper                 _mapper;

        public AuthServiceImpl(
            IAppUserRepository   userRepo,
            IRoleRepository      roleRepo,
            ITokenService        tokenService,
            IConfiguration       configuration,
            IHttpContextAccessor httpContextAccessor,
            IPublishEndpoint     publishEndpoint,
            ICacheService        cache,
            IMapper              mapper)
        {
            _userRepo            = userRepo;
            _roleRepo            = roleRepo;
            _tokenService        = tokenService;
            _configuration       = configuration;
            _httpContextAccessor = httpContextAccessor;
            _publishEndpoint     = publishEndpoint;
            _cache               = cache;
            _mapper              = mapper;
        }

        // ── Login ────────────────────────────────────────────────────────────────

        public async Task<LoginResponseDTO> LoginAsync(LoginRequestDTO request)
        {
            var user = await _userRepo.GetByEmailAsync(request.Email)
                ?? throw new BadRequestException("Email hoặc mật khẩu không đúng.");

            if (user.Status == UserStatus.Suspended)
                throw new BadRequestException("Tài khoản đã bị khóa bởi Admin.");

            if (user.Status == UserStatus.Deactivated)
                throw new BadRequestException("Tài khoản đã bị vô hiệu hoá.");

            if (user.Status == UserStatus.Pending)
                throw new BadRequestException($"Tài khoản chưa được xác thực email. Vui lòng kiểm tra hộp thư.|{user.Email}");

            if (!BCrypt.Net.BCrypt.Verify(request.Password, user.PasswordHash))
                throw new BadRequestException("Email hoặc mật khẩu không đúng.");

            var accessToken  = _tokenService.GenerateAccessToken(user);
            var refreshToken = _tokenService.GenerateRefreshToken(user);

            user.RefreshToken     = refreshToken;
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);
            await _userRepo.SaveChangesAsync();

            SetRefreshTokenCookie(refreshToken);
            await PushPermissionsToCacheAsync(user);

            return BuildLoginResponse(accessToken, user);
        }

        public async Task<LoginResponseDTO> ProcessSocialLoginAsync(string email, string fullName, string avatarUrl, string provider)
        {
            var emailLower = email.Trim().ToLowerInvariant();
            var user = await _userRepo.GetByEmailAsync(emailLower);

            if (user == null)
            {
                var defaultRole = await _roleRepo.GetByNameAsync("CANDIDATE")
                    ?? throw new BadRequestException("Role 'CANDIDATE' chưa tồn tại trong hệ thống.");

                var randomPassword = Guid.NewGuid().ToString("N");

                user = new AppUser
                {
                    Id           = Guid.NewGuid(),
                    Email        = emailLower,
                    Username     = fullName.Trim(),
                    PasswordHash = BCrypt.Net.BCrypt.HashPassword(randomPassword),
                    Status       = UserStatus.Active,
                    RoleId       = defaultRole.Id,
                    CreatedDate  = DateTimeOffset.UtcNow,
                };

                await _userRepo.AddAsync(user);

                await _publishEndpoint.Publish(new UserRegisteredEvent
                {
                    UserId       = user.Id,
                    Email        = user.Email,
                    Username     = user.Username,
                    Role         = "CANDIDATE",
                    RegisteredAt = user.CreatedDate.UtcDateTime,
                    Avatar       = avatarUrl
                });

                await _userRepo.SaveChangesAsync();

                // Gán Role sau khi SaveChanges để GenerateAccessToken sử dụng,
                // tránh việc EF Core hiểu nhầm là Role mới và lưu trùng khóa chính (PK_Roles).
                user.Role = defaultRole;
            }
            else
            {
                if (user.Status == UserStatus.Suspended)
                    throw new BadRequestException("Tài khoản đã bị khóa bởi Admin.");

                if (user.Status == UserStatus.Deactivated)
                    throw new BadRequestException("Tài khoản đã bị vô hiệu hoá.");

                if (user.Status == UserStatus.Pending)
                {
                    user.Status = UserStatus.Active;
                    user.LastModifiedDate = DateTimeOffset.UtcNow;
                    _userRepo.Update(user);
                    await _userRepo.SaveChangesAsync();
                }
            }

            var accessToken  = _tokenService.GenerateAccessToken(user);
            var refreshToken = _tokenService.GenerateRefreshToken(user);

            user.RefreshToken     = refreshToken;
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);
            await _userRepo.SaveChangesAsync();

            SetRefreshTokenCookie(refreshToken);
            await PushPermissionsToCacheAsync(user);

            return BuildLoginResponse(accessToken, user);
        }

        // ── Register ─────────────────────────────────────────────────────────────

        public async Task<RegisterResponseDTO> RegisterAsync(RegisterRequestDTO request)
        {

            if (await _userRepo.EmailExistsAsync(request.Email))
                throw new BadRequestException($"Email '{request.Email}' đã tồn tại.");

            // Double-check tại Service layer — tuyệt đối không cho tạo ADMIN qua self-register
            var requestedRole = request.Role.Trim().ToUpper();
            if (requestedRole == "ADMIN")
                throw new BadRequestException("Không được phép tự đăng ký tài khoản ADMIN.");

            var defaultRole = await _roleRepo.GetByNameAsync(requestedRole)
                ?? throw new BadRequestException($"Role '{requestedRole}' chưa tồn tại trong hệ thống.");

            var user = new AppUser
            {
                Id           = Guid.NewGuid(),
                Email        = request.Email.Trim().ToLowerInvariant(),
                Username     = request.Username.Trim(),
                PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
                Status       = UserStatus.Pending,
                RoleId       = defaultRole.Id,
                CreatedDate  = DateTimeOffset.UtcNow,
            };

            await _userRepo.AddAsync(user);

            // Sinh OTP và lưu Redis TTL 5 phút
            var otp = GenerateOtp();
            await _cache.SetAsync($"otp:register:{request.Email.ToLowerInvariant()}", otp, TimeSpan.FromMinutes(5));

            // Publish event UserRegistered (ProfileService tạo profile)
            await _publishEndpoint.Publish(new UserRegisteredEvent
            {
                UserId       = user.Id,
                Email        = user.Email,
                Username     = user.Username,
                Role         = request.Role,   // "CANDIDATE" hoặc "HR"
                RegisteredAt = user.CreatedDate.UtcDateTime
            });

            // Publish event gửi OTP email qua NotificationService
            await _publishEndpoint.Publish(new OtpRequestedEvent
            {
                Email   = user.Email,
                OtpCode = otp,
                OtpType = "REGISTER"
            });

            // 1 lần SaveChanges: lưu AppUser + OutboxMessages cùng Transaction
            await _userRepo.SaveChangesAsync();

            return new RegisterResponseDTO
            {
                Id          = user.Id,
                Email       = user.Email,
                Username    = request.Username,
                CreatedDate = user.CreatedDate,
            };
        }

        // ── Get Account ───────────────────────────────────────────────────────────

        public async Task<LoginResponseDTO> GetAccountAsync(string email)
        {
            var user = await _userRepo.GetByEmailAsync(email)
                ?? throw new NotFoundException($"Không tìm thấy user: {email}");

            return BuildLoginResponse(null, user);
        }

        // ── Refresh Token ─────────────────────────────────────────────────────────

        public async Task<LoginResponseDTO> RefreshTokenAsync(string refreshToken)
        {
            var principal = _tokenService.ValidateRefreshToken(refreshToken)
                ?? throw new BadRequestException("Refresh token không hợp lệ hoặc đã hết hạn.");

            var email = principal.Claims
                .FirstOrDefault(c => c.Type == System.Security.Claims.ClaimTypes.Email)?.Value
                ?? throw new BadRequestException("Refresh token không chứa email.");

            var user = await _userRepo.GetByRefreshTokenAsync(refreshToken)
                ?? throw new BadRequestException("Refresh token không khớp. Vui lòng đăng nhập lại.");

            if (user.Email != email)
                throw new BadRequestException("Refresh token không hợp lệ.");

            var newAccessToken  = _tokenService.GenerateAccessToken(user);
            var newRefreshToken = _tokenService.GenerateRefreshToken(user);

            user.RefreshToken     = newRefreshToken;
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);
            await _userRepo.SaveChangesAsync();

            SetRefreshTokenCookie(newRefreshToken);
            await PushPermissionsToCacheAsync(user);

            return BuildLoginResponse(newAccessToken, user);
        }

        // ── Logout ────────────────────────────────────────────────────────────────

        public async Task LogoutAsync(string email)
        {
            var user = await _userRepo.GetByEmailAsync(email);
            if (user == null) return;

            user.RefreshToken     = null;
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);
            await _userRepo.SaveChangesAsync();

            _httpContextAccessor.HttpContext?.Response.Cookies.Delete("refresh_token", new CookieOptions
            {
                HttpOnly = true,
                Secure   = true,
                SameSite = SameSiteMode.None
            });
            await _cache.RemoveAsync($"perm:{email}");
        }

        // ── Update Email ────────────────────────────────────────────────────────

        public async Task UpdateEmailAsync(Guid userId, UpdateEmailRequestDTO request)
        {
            var user = await _userRepo.GetByIdAsync(userId)
                ?? throw new NotFoundException("Tài khoản không tồn tại.");

            if (user.Email.Equals(request.Email, StringComparison.OrdinalIgnoreCase))
                return;

            if (!string.IsNullOrEmpty(request.CurrentPassword) && !string.IsNullOrEmpty(request.NewPassword))
            {
                if (!BCrypt.Net.BCrypt.Verify(request.CurrentPassword, user.PasswordHash))
                    throw new BadRequestException("Mật khẩu hiện tại không đúng.");

                user.PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.NewPassword);
            }

            if (await _userRepo.EmailExistsAsync(request.Email))
                throw new BadRequestException($"Email '{request.Email}' đã được người khác sử dụng.");

            user.Email            = request.Email;
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);

            await _publishEndpoint.Publish(new UserEmailUpdatedEvent
            {
                UserId    = user.Id,
                NewEmail  = user.Email,
                UpdatedAt = user.LastModifiedDate?.UtcDateTime ?? DateTime.UtcNow
            });

            await _userRepo.SaveChangesAsync();
        }

        // ── Update Username ─────────────────────────────────────────────────────

        public async Task UpdateUsernameAsync(Guid userId, UpdateUsernameRequest request)
        {
            var user = await _userRepo.GetByIdAsync(userId)
                ?? throw new NotFoundException("Tài khoản không tồn tại.");

            if (string.IsNullOrWhiteSpace(request.Username))
                throw new BadRequestException("Username không được để trống.");

            if (request.Username.Length < 3 || request.Username.Length > 50)
                throw new BadRequestException("Username phải từ 3 đến 50 ký tự.");

            user.Username = request.Username.Trim();
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);

            await _userRepo.SaveChangesAsync();
        }

        // ── Change Password ────────────────────────────────────────────────────

        public async Task ChangePasswordAsync(Guid userId, ChangePasswordRequest request)
        {
            var user = await _userRepo.GetByIdAsync(userId)
                ?? throw new NotFoundException("Tài khoản không tồn tại.");

            if (!BCrypt.Net.BCrypt.Verify(request.CurrentPassword, user.PasswordHash))
                throw new BadRequestException("Mật khẩu hiện tại không đúng.");

            user.PasswordHash     = BCrypt.Net.BCrypt.HashPassword(request.NewPassword);
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);
            await _userRepo.SaveChangesAsync();
        }

        // ── OTP ───────────────────────────────────────────────────────────────────

        public async Task VerifyEmailAsync(VerifyEmailRequest request)
        {
            var email = request.Email.ToLowerInvariant();

            if (request.OtpType == "RESET_PASSWORD")
            {
                // ── RESET_PASSWORD: chỉ kiểm tra OTP, không xóa (reset-password sẽ dùng lại) ──
                var cachedOtp = await _cache.GetAsync<string>($"otp:reset:{email}");

                if (string.IsNullOrEmpty(cachedOtp))
                    throw new BadRequestException("Mã OTP đã hết hạn hoặc không tồn tại. Vui lòng yêu cầu gửi lại.");

                if (cachedOtp != request.OtpCode)
                    throw new BadRequestException("Mã OTP không đúng.");

                // Không xóa key — để ResetPasswordAsync tự xóa sau khi đổi mật khẩu thành công
            }
            else
            {
                // ── REGISTER (default): xác thực OTP + kích hoạt tài khoản ──
                var cachedOtp = await _cache.GetAsync<string>($"otp:register:{email}");

                if (string.IsNullOrEmpty(cachedOtp))
                    throw new BadRequestException("Mã OTP đã hết hạn hoặc không tồn tại. Vui lòng yêu cầu gửi lại.");

                if (cachedOtp != request.OtpCode)
                    throw new BadRequestException("Mã OTP không đúng.");

                var user = await _userRepo.GetByEmailAsync(request.Email)
                    ?? throw new NotFoundException("Không tìm thấy tài khoản đang chờ xác thực.");

                if (user.Status != UserStatus.Pending)
                    throw new BadRequestException("Tài khoản này đã được xác thực trước đó.");

                user.Status           = UserStatus.Active;
                user.LastModifiedDate = DateTimeOffset.UtcNow;
                _userRepo.Update(user);
                await _userRepo.SaveChangesAsync();

                await _cache.RemoveAsync($"otp:register:{email}");
            }
        }


        public async Task SendOtpResetPasswordAsync(SendOtpRequest request)
        {
            var user = await _userRepo.GetByEmailAsync(request.Email)
                ?? throw new NotFoundException("Không tìm thấy tài khoản với email này.");

            if (user.Status == UserStatus.Pending)
                throw new BadRequestException("Tài khoản chưa được xác thực email.");

            var otp = GenerateOtp();
            await _cache.SetAsync($"otp:reset:{request.Email.ToLowerInvariant()}", otp, TimeSpan.FromMinutes(5));

            await _publishEndpoint.Publish(new OtpRequestedEvent
            {
                Email   = request.Email,
                OtpCode = otp,
                OtpType = "RESET_PASSWORD"
            });
        }

        public async Task ResetPasswordAsync(ResetPasswordRequest request)
        {
            var cachedOtp = await _cache.GetAsync<string>($"otp:reset:{request.Email.ToLowerInvariant()}");

            if (string.IsNullOrEmpty(cachedOtp))
                throw new BadRequestException("Mã OTP đã hết hạn hoặc không tồn tại. Vui lòng yêu cầu gửi lại.");

            if (cachedOtp != request.OtpCode)
                throw new BadRequestException("Mã OTP không đúng.");

            var user = await _userRepo.GetByEmailAsync(request.Email)
                ?? throw new NotFoundException("Không tìm thấy tài khoản.");

            user.PasswordHash     = BCrypt.Net.BCrypt.HashPassword(request.NewPassword);
            user.LastModifiedDate = DateTimeOffset.UtcNow;
            _userRepo.Update(user);
            await _userRepo.SaveChangesAsync();

            await _cache.RemoveAsync($"otp:reset:{request.Email.ToLowerInvariant()}");
        }

        public async Task ResendOtpAsync(SendOtpRequest request, string otpType)
        {
            var redisKey = otpType == "REGISTER"
                ? $"otp:register:{request.Email.ToLowerInvariant()}"
                : $"otp:reset:{request.Email.ToLowerInvariant()}";

            var existingOtp = await _cache.GetAsync<string>(redisKey);

            string otp;
            if (!string.IsNullOrEmpty(existingOtp))
                otp = existingOtp;
            else
            {
                otp = GenerateOtp();
                await _cache.SetAsync(redisKey, otp, TimeSpan.FromMinutes(5));
            }

            await _publishEndpoint.Publish(new OtpRequestedEvent
            {
                Email   = request.Email,
                OtpCode = otp,
                OtpType = otpType
            });

            await _userRepo.SaveChangesAsync();
        }

        // ── Private ───────────────────────────────────────────────────────────────

        private void SetRefreshTokenCookie(string refreshToken)
        {
            var expireSeconds = int.Parse(_configuration["Jwt:RefreshTokenExpireSeconds"] ?? "604800");
            // SameSite=None + Secure=true cho phép cookie hoạt động cross-site
            // (cần thiết khi Frontend chạy trên Vercel và Backend chạy qua Cloudflare Tunnel)
            _httpContextAccessor.HttpContext!.Response.Cookies.Append("refresh_token", refreshToken, new CookieOptions
            {
                HttpOnly  = true,
                Secure    = true,
                SameSite  = SameSiteMode.None,
                MaxAge    = TimeSpan.FromSeconds(expireSeconds)
            });
        }

        private async Task PushPermissionsToCacheAsync(AppUser user)
        {
            var permissions = user.Role?.Permissions?.Select(p => new PermissionCacheDto
            {
                ApiPath = p.ApiPath,
                Method  = p.Method,
                Module  = p.Module
            }).ToList() ?? new List<PermissionCacheDto>();

            var expireSeconds = int.Parse(_configuration["Jwt:AccessTokenExpireSeconds"] ?? "1800");

            await _cache.SetAsync(
                $"perm:{user.Email}",
                permissions,
                TimeSpan.FromSeconds(expireSeconds));
        }


        private LoginResponseDTO BuildLoginResponse(string? accessToken, AppUser user) => new()
        {
            AccessToken = accessToken,
            User        = _mapper.Map<UserLoginDto>(user),
        };

        private static string GenerateOtp()
            => Random.Shared.Next(100000, 999999).ToString();
    }
}


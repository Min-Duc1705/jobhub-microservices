using AuthService.Models.Request;
using AuthService.Services.Interface;
using CommonService.Annotations;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AuthService.Controllers
{
    [Route("api/v1/auth")]
    [ApiController]
    public class AuthController : ControllerBase
    {
        private readonly ITokenService _tokenService;
        private readonly IAuthService  _authService;

        public AuthController(ITokenService tokenService, IAuthService authService)
        {
            _tokenService = tokenService;
            _authService  = authService;
        }

        // POST /api/v1/auth/login
        [HttpPost("login")]
        [AllowAnonymous]
        [ApiMessage("Đăng nhập thành công")]
        public async Task<IActionResult> Login([FromBody] LoginRequestDTO request)
        {
            var result = await _authService.LoginAsync(request);
            return Ok(result);
        }

        // POST /api/v1/auth/register
        [HttpPost("register")]
        [AllowAnonymous]
        [ApiMessage("Đăng ký thành công. Vui lòng kiểm tra email để xác thực OTP")]
        public async Task<IActionResult> Register([FromBody] RegisterRequestDTO request)
        {
            var result = await _authService.RegisterAsync(request);
            return StatusCode(201, result);
        }

        // GET /api/v1/auth/account
        [HttpGet("account")]
        [Authorize]
        [ApiMessage("Lấy thông tin tài khoản thành công")]
        public async Task<IActionResult> GetAccount()
        {
            var email = _tokenService.GetCurrentUserEmail();
            if (string.IsNullOrEmpty(email)) return Unauthorized();

            var currentToken = Request.Headers["Authorization"]
                .ToString().Replace("Bearer ", "", StringComparison.OrdinalIgnoreCase).Trim();

            var result = await _authService.GetAccountAsync(email);
            result.AccessToken = string.IsNullOrEmpty(currentToken) ? null : currentToken;
            return Ok(result);
        }

        // PUT /api/v1/auth/email
        [HttpPut("email")]
        [Authorize]
        [ApiMessage("Cập nhật thông tin bảo mật thành công")]
        public async Task<IActionResult> UpdateEmail([FromBody] UpdateEmailRequestDTO request)
        {
            var userIdString = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdString) || !Guid.TryParse(userIdString, out var userId))
                return Unauthorized();

            await _authService.UpdateEmailAsync(userId, request);
            return Ok(new { message = "Đã cập nhật Email/Password thành công." });
        }

        // PUT /api/v1/auth/username
        [HttpPut("username")]
        [Authorize]
        [ApiMessage("Cập nhật tên hiển thị thành công")]
        public async Task<IActionResult> UpdateUsername([FromBody] UpdateUsernameRequest request)
        {
            var userIdString = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdString) || !Guid.TryParse(userIdString, out var userId))
                return Unauthorized();

            await _authService.UpdateUsernameAsync(userId, request);
            return Ok(new { message = "Đã cập nhật tên hiển thị thành công." });
        }

        // GET /api/v1/auth/refresh
        [HttpGet("refresh")]
        [AllowAnonymous]
        [ApiMessage("Refresh token thành công")]
        public async Task<IActionResult> RefreshToken()
        {
            var refreshToken = Request.Cookies["refresh_token"];
            if (string.IsNullOrEmpty(refreshToken))
                return BadRequest(new { message = "Không tìm thấy refresh token." });

            var result = await _authService.RefreshTokenAsync(refreshToken);
            return Ok(result);
        }

        // POST /api/v1/auth/logout
        [HttpPost("logout")]
        [Authorize]
        [ApiMessage("Đăng xuất thành công")]
        public async Task<IActionResult> Logout()
        {
            var email = _tokenService.GetCurrentUserEmail();
            if (!string.IsNullOrEmpty(email))
                await _authService.LogoutAsync(email);

            return Ok((object?)null);
        }

        // PATCH /api/v1/auth/change-password
        [HttpPatch("change-password")]
        [Authorize]
        [ApiMessage("Đổi mật khẩu thành công")]
        public async Task<IActionResult> ChangePassword([FromBody] ChangePasswordRequest request)
        {
            var userIdString = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdString) || !Guid.TryParse(userIdString, out var userId))
                return Unauthorized();

            await _authService.ChangePasswordAsync(userId, request);
            return Ok(new { message = "Đổi mật khẩu thành công." });
        }

        // ── OTP Endpoints ─────────────────────────────────────────────────────────

        // POST /api/v1/auth/verify-email?otpType=REGISTER|RESET_PASSWORD
        [HttpPost("verify-email")]
        [AllowAnonymous]
        [ApiMessage("Xác thực email thành công")]
        public async Task<IActionResult> VerifyEmail(
            [FromBody] VerifyEmailRequest request,
            [FromQuery] string otpType = "REGISTER")
        {
            request.OtpType = otpType; // query param override body field (an toàn hơn)
            await _authService.VerifyEmailAsync(request);
            return Ok(new { message = "Xác thực thành công." });
        }

        // POST /api/v1/auth/send-otp-reset
        [HttpPost("send-otp-reset")]
        [AllowAnonymous]
        [ApiMessage("Đã gửi mã OTP đặt lại mật khẩu")]
        public async Task<IActionResult> SendOtpReset([FromBody] SendOtpRequest request)
        {
            await _authService.SendOtpResetPasswordAsync(request);
            return Ok(new { message = $"Mã OTP đặt lại mật khẩu đã được gửi tới {request.Email}." });
        }

        // POST /api/v1/auth/reset-password
        [HttpPost("reset-password")]
        [AllowAnonymous]
        [ApiMessage("Đặt lại mật khẩu thành công")]
        public async Task<IActionResult> ResetPassword([FromBody] ResetPasswordRequest request)
        {
            await _authService.ResetPasswordAsync(request);
            return Ok(new { message = "Mật khẩu đã được đặt lại thành công." });
        }

        // POST /api/v1/auth/resend-otp
        [HttpPost("resend-otp")]
        [AllowAnonymous]
        [ApiMessage("Đã gửi lại mã OTP")]
        public async Task<IActionResult> ResendOtp([FromBody] SendOtpRequest request, [FromQuery] string otpType = "REGISTER")
        {
            if (otpType != "REGISTER" && otpType != "RESET_PASSWORD")
                return BadRequest(new { message = "otpType không hợp lệ. Chỉ chấp nhận: REGISTER | RESET_PASSWORD" });

            await _authService.ResendOtpAsync(request, otpType);
            return Ok(new { message = $"Mã OTP đã được gửi lại tới {request.Email}." });
        }
    }
}

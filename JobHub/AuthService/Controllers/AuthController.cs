using System.Net.Http.Headers;
using System.Text.Json;
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

        // POST /api/v1/auth/google
        [HttpPost("google")]
        [AllowAnonymous]
        [ApiMessage("Đăng nhập Google thành công")]
        public async Task<IActionResult> LoginWithGoogle([FromBody] GoogleLoginRequestDTO request, [FromServices] HttpClient httpClient)
        {
            if (string.IsNullOrEmpty(request.AccessToken))
                return BadRequest(new { message = "AccessToken không được để trống." });

            var googleUserInfoUrl = $"https://www.googleapis.com/oauth2/v3/userinfo?access_token={request.AccessToken}";
            var response = await httpClient.GetAsync(googleUserInfoUrl);
            if (!response.IsSuccessStatusCode)
            {
                return BadRequest(new { message = "Xác thực token Google thất bại." });
            }

            var content = await response.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(content);
            var root = doc.RootElement;

            string? email = null;
            if (root.TryGetProperty("email", out var emailProp))
                email = emailProp.GetString();

            string? name = null;
            if (root.TryGetProperty("name", out var nameProp))
                name = nameProp.GetString();

            string? picture = null;
            if (root.TryGetProperty("picture", out var pictureProp))
                picture = pictureProp.GetString();

            if (string.IsNullOrEmpty(email))
            {
                return BadRequest(new { message = "Không thể lấy thông tin email từ tài khoản Google." });
            }

            var result = await _authService.ProcessSocialLoginAsync(
                email: email,
                fullName: name ?? email.Split('@')[0],
                avatarUrl: picture ?? string.Empty,
                provider: "GOOGLE"
            );

            return Ok(result);
        }

        // POST /api/v1/auth/github
        [HttpPost("github")]
        [AllowAnonymous]
        [ApiMessage("Đăng nhập GitHub thành công")]
        public async Task<IActionResult> LoginWithGithub([FromBody] GithubLoginRequestDTO request, [FromServices] HttpClient httpClient, [FromServices] IConfiguration configuration)
        {
            if (string.IsNullOrEmpty(request.Code))
                return BadRequest(new { message = "Mã code GitHub không được để trống." });

            var clientId = configuration["GitHub:ClientId"];
            var clientSecret = configuration["GitHub:ClientSecret"];

            if (string.IsNullOrEmpty(clientId) || string.IsNullOrEmpty(clientSecret))
                return BadRequest(new { message = "Cấu hình GitHub trên máy chủ không hợp lệ." });

            // 1. Exchange code for access token via POST https://github.com/login/oauth/access_token
            var tokenRequestParams = new Dictionary<string, string>
            {
                { "client_id", clientId },
                { "client_secret", clientSecret },
                { "code", request.Code }
            };

            var tokenRequest = new HttpRequestMessage(HttpMethod.Post, "https://github.com/login/oauth/access_token")
            {
                Content = new FormUrlEncodedContent(tokenRequestParams)
            };
            tokenRequest.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

            var tokenResponse = await httpClient.SendAsync(tokenRequest);
            if (!tokenResponse.IsSuccessStatusCode)
                return BadRequest(new { message = "Lấy token từ GitHub thất bại." });

            var tokenContent = await tokenResponse.Content.ReadAsStringAsync();
            using var tokenDoc = JsonDocument.Parse(tokenContent);
            var tokenRoot = tokenDoc.RootElement;

            string? githubAccessToken = null;
            if (tokenRoot.TryGetProperty("access_token", out var tokenProp))
                githubAccessToken = tokenProp.GetString();

            if (string.IsNullOrEmpty(githubAccessToken))
                return BadRequest(new { message = "Mã xác thực GitHub không hợp lệ hoặc đã hết hạn." });

            // 2. Fetch User Profile from GitHub API
            var userRequest = new HttpRequestMessage(HttpMethod.Get, "https://api.github.com/user");
            userRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", githubAccessToken);
            userRequest.Headers.UserAgent.Add(new ProductInfoHeaderValue("JobHub", "1.0"));

            var userResponse = await httpClient.SendAsync(userRequest);
            if (!userResponse.IsSuccessStatusCode)
                return BadRequest(new { message = "Lấy thông tin profile từ GitHub thất bại." });

            var userContent = await userResponse.Content.ReadAsStringAsync();
            using var userDoc = JsonDocument.Parse(userContent);
            var userRoot = userDoc.RootElement;

            string? email = null;
            if (userRoot.TryGetProperty("email", out var emailProp))
                email = emailProp.GetString();

            string? loginName = null;
            if (userRoot.TryGetProperty("login", out var loginProp))
                loginName = loginProp.GetString();

            string? name = null;
            if (userRoot.TryGetProperty("name", out var nameProp))
                name = nameProp.GetString();

            string? avatarUrl = null;
            if (userRoot.TryGetProperty("avatar_url", out var avatarProp))
                avatarUrl = avatarProp.GetString();

            // 3. GitHub may hide email. Try user/emails API if email is empty
            if (string.IsNullOrEmpty(email))
            {
                var emailRequest = new HttpRequestMessage(HttpMethod.Get, "https://api.github.com/user/emails");
                emailRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", githubAccessToken);
                emailRequest.Headers.UserAgent.Add(new ProductInfoHeaderValue("JobHub", "1.0"));

                var emailResponse = await httpClient.SendAsync(emailRequest);
                if (emailResponse.IsSuccessStatusCode)
                {
                    var emailContent = await emailResponse.Content.ReadAsStringAsync();
                    using var emailDoc = JsonDocument.Parse(emailContent);
                    if (emailDoc.RootElement.ValueKind == JsonValueKind.Array)
                    {
                        foreach (var element in emailDoc.RootElement.EnumerateArray())
                        {
                            bool isPrimary = false;
                            bool isVerified = false;
                            if (element.TryGetProperty("primary", out var primaryProp))
                                isPrimary = primaryProp.GetBoolean();
                            if (element.TryGetProperty("verified", out var verifiedProp))
                                isVerified = verifiedProp.GetBoolean();

                            if (isPrimary && isVerified && element.TryGetProperty("email", out var eProp))
                            {
                                email = eProp.GetString();
                                break;
                            }
                        }

                        if (string.IsNullOrEmpty(email) && emailDoc.RootElement.GetArrayLength() > 0)
                        {
                            var firstElement = emailDoc.RootElement[0];
                            if (firstElement.TryGetProperty("email", out var eProp))
                                email = eProp.GetString();
                        }
                    }
                }
            }

            if (string.IsNullOrEmpty(email))
            {
                return BadRequest(new { message = "Yêu cầu quyền truy cập địa chỉ Email trên GitHub của bạn." });
            }

            var result = await _authService.ProcessSocialLoginAsync(
                email: email,
                fullName: name ?? loginName ?? email.Split('@')[0],
                avatarUrl: avatarUrl ?? string.Empty,
                provider: "GITHUB"
            );

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

using AuthService.Models.Request;
using AuthService.Models.Response;

namespace AuthService.Services.Interface
{
    public interface IAuthService
    {
        Task<LoginResponseDTO>    LoginAsync(LoginRequestDTO request);
        Task<RegisterResponseDTO> RegisterAsync(RegisterRequestDTO request);
        Task<LoginResponseDTO>    GetAccountAsync(string email);
        Task<LoginResponseDTO>    RefreshTokenAsync(string refreshToken);
        Task                      LogoutAsync(string email);

        Task UpdateEmailAsync(Guid userId, UpdateEmailRequestDTO request);
        Task ChangePasswordAsync(Guid userId, ChangePasswordRequest request);

        // ── OTP ──────────────────────────────────────────────────────────────
        Task VerifyEmailAsync(VerifyEmailRequest request);
        Task SendOtpResetPasswordAsync(SendOtpRequest request);
        Task ResetPasswordAsync(ResetPasswordRequest request);
        Task ResendOtpAsync(SendOtpRequest request, string otpType);
    }
}

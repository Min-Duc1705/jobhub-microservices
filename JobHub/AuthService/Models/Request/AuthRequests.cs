namespace AuthService.Models.Request
{
    public class LoginRequestDTO
    {
        public string Email    { get; set; } = string.Empty;
        public string Password { get; set; } = string.Empty;
    }

    public class RegisterRequestDTO
    {
        public string Email    { get; set; } = string.Empty;
        public string Username { get; set; } = string.Empty;
        public string Password { get; set; } = string.Empty;
        /// <summary>CANDIDATE hoặc HR. Mặc định CANDIDATE nếu không truyền. Nghiêm cấm ADMIN.</summary>
        public string Role     { get; set; } = "CANDIDATE";
    }

    public class UpdateEmailRequestDTO
    {
        public string  Email           { get; set; } = string.Empty;
        public string? CurrentPassword { get; set; }
        public string? NewPassword     { get; set; }
    }

    public class ChangePasswordRequest
    {
        public string CurrentPassword { get; set; } = string.Empty;
        public string NewPassword     { get; set; } = string.Empty;
    }

    public class VerifyEmailRequest
    {
        public string Email   { get; set; } = string.Empty;
        public string OtpCode { get; set; } = string.Empty;
        /// <summary>REGISTER (default) hoặc RESET_PASSWORD</summary>
        public string OtpType { get; set; } = "REGISTER";
    }

    public class SendOtpRequest
    {
        public string Email { get; set; } = string.Empty;
    }

    public class ResetPasswordRequest
    {
        public string Email       { get; set; } = string.Empty;
        public string OtpCode     { get; set; } = string.Empty;
        public string NewPassword { get; set; } = string.Empty;
    }

    public class UpdateUsernameRequest
    {
        public string Username { get; set; } = string.Empty;
    }

    public class GoogleLoginRequestDTO
    {
        public string AccessToken { get; set; } = string.Empty;
    }

    public class GithubLoginRequestDTO
    {
        public string Code { get; set; } = string.Empty;
    }
}

using AuthService.Models;
using CommonService.Repository;

namespace AuthService.Repositories.Interface
{
    /// <summary>
    /// Kế thừa IGenericRepository để có CRUD + Specification.
    /// Thêm các method đặc thù của AppUser: tìm theo email, theo refresh token.
    /// </summary>
    public interface IAppUserRepository : IGenericRepository<AppUser>
    {
        /// <summary>Tìm user theo email hoặc username (include Role + Permissions).</summary>
        Task<AppUser?> GetByEmailAsync(string emailOrUsername);

        /// <summary>Tìm user theo refresh token để verify khi refresh JWT.</summary>
        Task<AppUser?> GetByRefreshTokenAsync(string refreshToken);

        /// <summary>Kiểm tra email đã tồn tại chưa.</summary>
        Task<bool> EmailExistsAsync(string email);
    }
}

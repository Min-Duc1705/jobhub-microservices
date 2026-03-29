using CommonService.Models.Interface;

namespace CommonService.Models.Interface
{
    /// <summary>
    /// Interface gộp: bao hàm toàn bộ tracking (ngày, người dùng) và soft delete.
    /// Chỉ cần implement interface này là đủ tất cả.
    /// </summary>
    public interface IAuditable : IDateTracking, IUserTracking, ISoftDelete
    {
    }
}

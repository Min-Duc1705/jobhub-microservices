using CommonService.Models.Interface;

namespace CommonService.Models;

/// <summary>
/// Base class đầy đủ cho các Entity cần audit tracking và soft delete.
/// Kế thừa EntityBase (có Id) và implement IAuditable (có Date, User, SoftDelete).
/// </summary>
public abstract class EntityAuditableBase<T> : EntityBase<T>, IAuditable
{
    // --- IDateTracking ---
    public DateTimeOffset  CreatedDate      { get; set; }
    public DateTimeOffset? LastModifiedDate { get; set; }

    // --- IUserTracking ---
    public string  CreatedBy      { get; set; } = string.Empty;
    public string? LastModifiedBy { get; set; }

    // --- ISoftDelete ---
    public bool            IsDeleted { get; set; } = false;
    public DateTimeOffset? DeletedAt { get; set; }
}

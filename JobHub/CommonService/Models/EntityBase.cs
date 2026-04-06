using CommonService.Models.Interface;

namespace CommonService.Models;

public abstract class EntityBase<T> : IEntityBase<T>
{
    public T Id { get; set; } = default!;
}
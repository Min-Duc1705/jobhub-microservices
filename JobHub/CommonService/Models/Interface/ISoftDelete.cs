namespace CommonService.Models.Interface
{
    public interface ISoftDelete
    {
        bool IsDeleted { get; set; }
        DateTimeOffset? DeletedAt { get; set; }
    }
}

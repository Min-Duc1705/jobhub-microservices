namespace CommonService.Common;

/// <summary>
/// DTO chuẩn cho response phân trang — Generic để type-safe.
/// Dùng chung cho tất cả microservices. Cấu trúc khớp với MicroserviceShop.
/// </summary>
public class ResultPaginationDto<T>
{
    public MetaInfo?          Meta   { get; set; }
    public IReadOnlyList<T>?  Result { get; set; }

    public ResultPaginationDto(IReadOnlyList<T> items, int page, int pageSize, int totalRecords)
    {
        Meta = new MetaInfo
        {
            Page     = page,
            PageSize = pageSize,
            Total    = totalRecords,
            Pages    = pageSize > 0 ? (int)Math.Ceiling(totalRecords / (double)pageSize) : 1
        };
        Result = items;
    }

    public class MetaInfo
    {
        public int  Page     { get; set; }
        public int  PageSize { get; set; }
        public int  Pages    { get; set; }
        public long Total    { get; set; }
    }
}

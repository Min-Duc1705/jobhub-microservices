using CommonService.Repository;
using CompanyService.Models;

namespace CompanyService.Repositories.Interface;

/// <summary>
/// Repository cho Company — kế thừa toàn bộ CRUD + Specification từ IGenericRepository.
/// Chỉ khai báo thêm method đặc thù của Company.
/// </summary>
public interface ICompanyRepository : IGenericRepository<Company>
{
    /// <summary>Tìm công ty theo mã số thuế (dùng để check trùng khi tạo/sửa).</summary>
    Task<Company?> GetByTaxCodeAsync(string taxCode);
}

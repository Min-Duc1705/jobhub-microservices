using CommonService.Common;
using CompanyService.Models.Request;
using CompanyService.Models.Response;

namespace CompanyService.Services.Interface;

public interface ICompanyService
{
    Task<ResultPaginationDto<CompanyResponse>> GetAllAsync(CompanyFilterRequest filter);
    Task<CompanyResponse> GetByIdAsync(Guid id);
    Task<CompanyResponse> CreateAsync(CreateCompanyRequest request);
    Task<CompanyResponse> UpdateAsync(Guid id, UpdateCompanyRequest request);
    Task DeleteAsync(Guid id);
    Task<CompanyResponse> VerifyAsync(Guid id);
    Task<CommonService.Import.ImportResult<ImportCompanyDto>> ImportAsync(Microsoft.AspNetCore.Http.IFormFile file);
}

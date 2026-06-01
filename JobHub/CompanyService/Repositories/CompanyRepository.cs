using CommonService.Repository;
using CompanyService.Data;
using CompanyService.Models;
using CompanyService.Repositories.Interface;
using Microsoft.EntityFrameworkCore;

namespace CompanyService.Repositories;

/// <summary>
/// Kế thừa GenericRepository để có sẵn: GetByIdAsync, GetAllAsync, AddAsync, Update,
/// Delete (soft), SaveChangesAsync, ListAsync(spec), CountAsync(spec).
/// Chỉ triển khai thêm method đặc thù của Company.
/// </summary>
public class CompanyRepository : GenericRepository<CompanyDbContext, Company>, ICompanyRepository
{
    public CompanyRepository(CompanyDbContext context) : base(context) { }

    public async Task<Company?> GetByTaxCodeAsync(string taxCode)
        => await _dbSet.FirstOrDefaultAsync(c => c.TaxCode == taxCode && !c.IsDeleted);
}

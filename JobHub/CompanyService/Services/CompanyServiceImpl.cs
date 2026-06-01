using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using CompanyService.Models;
using CompanyService.Models.Request;
using CompanyService.Models.Response;
using CompanyService.Repositories.Interface;
using CompanyService.Services.Interface;
using CompanyService.Specifications;

namespace CompanyService.Services;

public class CompanyServiceImpl : ICompanyService
{
    private readonly ICompanyRepository _companyRepo;
    private readonly IMapper            _mapper;

    public CompanyServiceImpl(ICompanyRepository companyRepo, IMapper mapper)
    {
        _companyRepo = companyRepo;
        _mapper      = mapper;
    }

    // ── GET danh sách có phân trang ─────────────────────────────────────────
    public async Task<ResultPaginationDto<CompanyResponse>> GetAllAsync(CompanyFilterRequest filter)
    {
        var spec      = new CompanyFilterSpec(
            filter.SearchTerm, filter.Industry, filter.CompanySize,
            filter.IsVerified, filter.SortBy, filter.IsDescending,
            filter.PageNumber, filter.PageSize);

        var countSpec = new CompanyFilterCountSpec(
            filter.SearchTerm, filter.Industry, filter.CompanySize, filter.IsVerified);

        // ListAsync & CountAsync đến từ IGenericRepository (GenericRepository)
        var items      = await _companyRepo.ListAsync(spec);
        var totalCount = await _companyRepo.CountAsync(countSpec);

        return new ResultPaginationDto<CompanyResponse>(
            _mapper.Map<List<CompanyResponse>>(items),
            filter.PageNumber, filter.PageSize, totalCount);
    }

    // ── GET theo ID ─────────────────────────────────────────────────────────
    public async Task<CompanyResponse> GetByIdAsync(Guid id)
    {
        var company = await _companyRepo.GetByIdAsync(id);
        if (company == null || company.IsDeleted)
            throw new NotFoundException($"Không tìm thấy công ty với ID: {id}");

        return _mapper.Map<CompanyResponse>(company);
    }

    // ── Tạo mới ─────────────────────────────────────────────────────────────
    public async Task<CompanyResponse> CreateAsync(CreateCompanyRequest request)
    {
        if (!string.IsNullOrWhiteSpace(request.TaxCode))
        {
            var existing = await _companyRepo.GetByTaxCodeAsync(request.TaxCode);
            if (existing != null)
                throw new BadRequestException($"Mã số thuế '{request.TaxCode}' đã tồn tại trong hệ thống.");
        }

        var company = _mapper.Map<Company>(request);
        company.IsVerified = false;

        await _companyRepo.AddAsync(company);
        await _companyRepo.SaveChangesAsync();

        return _mapper.Map<CompanyResponse>(company);
    }

    // ── Cập nhật ────────────────────────────────────────────────────────────
    public async Task<CompanyResponse> UpdateAsync(Guid id, UpdateCompanyRequest request)
    {
        var company = await _companyRepo.GetByIdAsync(id);
        if (company == null || company.IsDeleted)
            throw new NotFoundException($"Không tìm thấy công ty với ID: {id}");

        if (!string.IsNullOrWhiteSpace(request.TaxCode))
        {
            var conflict = await _companyRepo.GetByTaxCodeAsync(request.TaxCode);
            if (conflict != null && conflict.Id != id)
                throw new BadRequestException($"Mã số thuế '{request.TaxCode}' đã được đăng ký bởi công ty khác.");
        }

        _mapper.Map(request, company);
        _companyRepo.Update(company);
        await _companyRepo.SaveChangesAsync();

        return _mapper.Map<CompanyResponse>(company);
    }

    // ── Xóa mềm ────────────────────────────────────────────────────────────
    public async Task DeleteAsync(Guid id)
    {
        var company = await _companyRepo.GetByIdAsync(id);
        if (company == null || company.IsDeleted)
            throw new NotFoundException($"Không tìm thấy công ty với ID: {id}");

        _companyRepo.Delete(company);          // soft delete từ GenericRepository
        await _companyRepo.SaveChangesAsync();
    }

    // ── Admin xác minh doanh nghiệp ─────────────────────────────────────────
    public async Task<CompanyResponse> VerifyAsync(Guid id)
    {
        var company = await _companyRepo.GetByIdAsync(id);
        if (company == null || company.IsDeleted)
            throw new NotFoundException($"Không tìm thấy công ty với ID: {id}");

        if (company.IsVerified)
            throw new BadRequestException("Công ty này đã được xác minh rồi.");

        company.IsVerified = true;
        _companyRepo.Update(company);
        await _companyRepo.SaveChangesAsync();

        return _mapper.Map<CompanyResponse>(company);
    }
}

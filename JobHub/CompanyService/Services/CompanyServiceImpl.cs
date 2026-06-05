using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using CommonService.Storage;
using CompanyService.Models;
using CompanyService.Models.Request;
using CompanyService.Models.Response;
using CompanyService.Repositories.Interface;
using CompanyService.Services.Interface;
using CompanyService.Specifications;
using Microsoft.Extensions.Options;

using CommonService.Import;

namespace CompanyService.Services;

public class CompanyServiceImpl : ICompanyService
{
    private readonly ICompanyRepository     _companyRepo;
    private readonly IMapper                _mapper;
    private readonly MinioSettings          _minioSettings;
    private readonly IExcelCsvImportService _importService;

    public CompanyServiceImpl(
        ICompanyRepository companyRepo, 
        IMapper mapper, 
        IOptions<MinioSettings> minioSettings,
        IExcelCsvImportService importService)
    {
        _companyRepo = companyRepo;
        _mapper      = mapper;
        _minioSettings = minioSettings.Value;
        _importService = importService;
    }

    private CompanyResponse FormatUrls(CompanyResponse response)
    {
        if (response == null) return null!;
        response.Logo = MinioUrlHelper.ToAbsoluteUrl(response.Logo, _minioSettings, "companies");
        response.CoverImage = MinioUrlHelper.ToAbsoluteUrl(response.CoverImage, _minioSettings, "companies");
        response.ActivityImages = MinioUrlHelper.ToAbsoluteUrls(response.ActivityImages, _minioSettings, "companies");
        return response;
    }

    private List<CompanyResponse> FormatUrls(List<CompanyResponse> responses)
    {
        if (responses == null) return null!;
        foreach (var r in responses)
        {
            FormatUrls(r);
        }
        return responses;
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
            FormatUrls(_mapper.Map<List<CompanyResponse>>(items)),
            filter.PageNumber, filter.PageSize, totalCount);
    }

    // ── GET theo ID ─────────────────────────────────────────────────────────
    public async Task<CompanyResponse> GetByIdAsync(Guid id)
    {
        var company = await _companyRepo.GetByIdAsync(id);
        if (company == null || company.IsDeleted)
            throw new NotFoundException($"Không tìm thấy công ty với ID: {id}");

        return FormatUrls(_mapper.Map<CompanyResponse>(company));
    }

    // ── Tạo mới ─────────────────────────────────────────────────────────────
    public async Task<CompanyResponse> CreateAsync(CreateCompanyRequest request)
    {
        request.Logo = MinioUrlHelper.ToRelativePath(request.Logo);
        request.CoverImage = MinioUrlHelper.ToRelativePath(request.CoverImage);
        request.ActivityImages = MinioUrlHelper.ToRelativePaths(request.ActivityImages);

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

        return FormatUrls(_mapper.Map<CompanyResponse>(company));
    }

    // ── Cập nhật ────────────────────────────────────────────────────────────
    public async Task<CompanyResponse> UpdateAsync(Guid id, UpdateCompanyRequest request)
    {
        request.Logo = MinioUrlHelper.ToRelativePath(request.Logo);
        request.CoverImage = MinioUrlHelper.ToRelativePath(request.CoverImage);
        request.ActivityImages = MinioUrlHelper.ToRelativePaths(request.ActivityImages);

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

        return FormatUrls(_mapper.Map<CompanyResponse>(company));
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

        return FormatUrls(_mapper.Map<CompanyResponse>(company));
    }

    public async Task<ImportResult<ImportCompanyDto>> ImportAsync(Microsoft.AspNetCore.Http.IFormFile file)
    {
        var importResult = await _importService.ImportAsync<ImportCompanyDto>(file);
        if (!importResult.IsSuccess)
        {
            return importResult;
        }

        var validatedList = new List<ImportCompanyDto>();
        var seenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var seenTaxCodes = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (int i = 0; i < importResult.Data.Count; i++)
        {
            var req = importResult.Data[i];
            var rowIndex = i + 2;

            if (req == null) continue;

            if (string.IsNullOrWhiteSpace(req.Name))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "Name", ErrorMessage = "Tên công ty không được để trống." });
                continue;
            }

            var name = req.Name.Trim();
            if (seenNames.Contains(name))
            {
                importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "Name", ErrorMessage = $"Tên công ty '{req.Name}' bị trùng lặp trong file." });
                continue;
            }
            seenNames.Add(name);

            if (!string.IsNullOrWhiteSpace(req.TaxCode))
            {
                var taxCode = req.TaxCode.Trim();
                if (seenTaxCodes.Contains(taxCode))
                {
                    importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "TaxCode", ErrorMessage = $"Mã số thuế '{req.TaxCode}' bị trùng lặp trong file." });
                    continue;
                }
                seenTaxCodes.Add(taxCode);

                var existing = await _companyRepo.GetByTaxCodeAsync(taxCode);
                if (existing != null)
                {
                    importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "TaxCode", ErrorMessage = $"Mã số thuế '{req.TaxCode}' đã tồn tại trong hệ thống." });
                    continue;
                }
            }

            if (!string.IsNullOrWhiteSpace(req.CompanySize))
            {
                if (!Enum.TryParse<CompanyService.Models.Enums.CompanySize>(req.CompanySize.Trim(), true, out _))
                {
                    importResult.Errors.Add(new ValidationError { RowIndex = rowIndex, ColumnName = "CompanySize", ErrorMessage = $"Quy mô '{req.CompanySize}' không hợp lệ. Cho phép: STARTUP, SME, ENTERPRISE." });
                    continue;
                }
            }

            validatedList.Add(req);
        }

        if (!importResult.IsSuccess)
        {
            importResult.Data.Clear();
            return importResult;
        }

        foreach (var req in validatedList)
        {
            CompanyService.Models.Enums.CompanySize? size = null;
            if (!string.IsNullOrWhiteSpace(req.CompanySize) && Enum.TryParse<CompanyService.Models.Enums.CompanySize>(req.CompanySize.Trim(), true, out var parsedSize))
            {
                size = parsedSize;
            }

            var company = new Company
            {
                Name         = req.Name.Trim(),
                Description  = req.Description,
                Address      = req.Address,
                Industry     = req.Industry,
                CompanySize  = size,
                Website      = req.Website,
                ContactEmail = req.ContactEmail,
                TaxCode      = req.TaxCode?.Trim(),
                IsVerified   = true
            };
            await _companyRepo.AddAsync(company);
        }
        await _companyRepo.SaveChangesAsync();

        importResult.Data = validatedList;
        return importResult;
    }
}

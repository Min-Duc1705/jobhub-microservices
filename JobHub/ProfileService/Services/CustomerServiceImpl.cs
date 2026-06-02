using AutoMapper;
using CommonService.Common;
using CommonService.Exceptions;
using CommonService.Storage;
using ProfileService.Models.Request;
using ProfileService.Models.Response;
using ProfileService.Repositories.Interface;
using ProfileService.Services.Interface;
using ProfileService.Specifications;
using Microsoft.Extensions.Options;

namespace ProfileService.Services;

public class CustomerServiceImpl : ICustomerService
{
    private readonly ICustomerRepository _customerRepository;
    private readonly IMapper             _mapper;
    private readonly MinioSettings      _minioSettings;

    public CustomerServiceImpl(ICustomerRepository customerRepository, IMapper mapper, IOptions<MinioSettings> minioSettings)
    {
        _customerRepository = customerRepository;
        _mapper             = mapper;
        _minioSettings = minioSettings.Value;
    }

    private CustomerResponse FormatUrls(CustomerResponse response)
    {
        if (response == null) return null!;
        response.Avatar = MinioUrlHelper.ToAbsoluteUrl(response.Avatar, _minioSettings, "avatars");
        return response;
    }

    private List<CustomerResponse> FormatUrls(List<CustomerResponse> responses)
    {
        if (responses == null) return null!;
        foreach (var r in responses)
        {
            FormatUrls(r);
        }
        return responses;
    }

    public async Task<ResultPaginationDto<CustomerResponse>> GetAllAsync(CustomerFilterRequest filter)
    {
        var spec      = new CustomerFilterSpec(filter.SearchTerm, filter.Type, filter.SortBy, filter.IsDescending, filter.PageNumber, filter.PageSize);
        var countSpec = new CustomerFilterCountSpec(filter.SearchTerm, filter.Type);

        var items      = await _customerRepository.ListAsync(spec);
        var totalCount = await _customerRepository.CountAsync(countSpec);

        return new ResultPaginationDto<CustomerResponse>(
            FormatUrls(_mapper.Map<List<CustomerResponse>>(items)),
            filter.PageNumber, filter.PageSize, (int)totalCount);
    }

    public async Task<CustomerResponse> GetMyProfileAsync(Guid appUserId)
    {
        var customer = await _customerRepository.GetByAppUserIdAsync(appUserId);
        if (customer == null)
            throw new NotFoundException("Không tìm thấy hồ sơ cá nhân.");

        return FormatUrls(_mapper.Map<CustomerResponse>(customer));
    }

    public async Task<CustomerResponse> UpdateMyProfileAsync(Guid appUserId, UpdateCustomerRequest request)
    {
        request.Avatar = MinioUrlHelper.ToRelativePath(request.Avatar);

        var customer = await _customerRepository.GetByAppUserIdAsync(appUserId);
        if (customer == null)
            throw new NotFoundException("Không tìm thấy hồ sơ cá nhân để cập nhật.");

        _mapper.Map(request, customer);
        _customerRepository.Update(customer);
        await _customerRepository.SaveChangesAsync();

        return FormatUrls(_mapper.Map<CustomerResponse>(customer));
    }

    public async Task<CustomerResponse> GetProfileByIdAsync(Guid customerId)
    {
        var customer = await _customerRepository.GetEntityWithSpec(new CustomerByIdSpec(customerId));
        if (customer == null)
            throw new NotFoundException("Không tìm thấy hồ sơ cá nhân.");

        return FormatUrls(_mapper.Map<CustomerResponse>(customer));
    }

    public async Task<CustomerResponse> AdminUpdateCustomerAsync(Guid customerId, UpdateCustomerRequest request)
    {
        request.Avatar = MinioUrlHelper.ToRelativePath(request.Avatar);

        var customer = await _customerRepository.GetEntityWithSpec(new CustomerByIdSpec(customerId));
        if (customer == null)
            throw new NotFoundException("Không tìm thấy hồ sơ cá nhân cần cập nhật.");

        _mapper.Map(request, customer);
        _customerRepository.Update(customer);
        await _customerRepository.SaveChangesAsync();

        return FormatUrls(_mapper.Map<CustomerResponse>(customer));
    }

    public async Task AdminDeleteCustomerAsync(Guid customerId)
    {
        var customer = await _customerRepository.GetEntityWithSpec(new CustomerByIdSpec(customerId));
        if (customer == null)
            throw new NotFoundException("Không tìm thấy hồ sơ cá nhân cần xóa.");

        _customerRepository.Delete(customer);
        await _customerRepository.SaveChangesAsync();
    }
}

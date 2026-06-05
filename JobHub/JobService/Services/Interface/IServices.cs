using CommonService.Common;
using CommonService.Import;
using JobService.Models.Request;
using JobService.Models.Response;
using Microsoft.AspNetCore.Http;

namespace JobService.Services.Interface;

public interface IJobService
{
    Task<ResultPaginationDto<JobResponse>> GetAllAsync(JobFilterRequest filter);
    Task<ResultPaginationDto<JobResponse>> GetAllForAdminAsync(AdminJobFilterRequest filter);
    Task<JobResponse> GetByIdAsync(Guid id, bool incrementView = true);
    Task<JobResponse> CreateAsync(Guid customerId, CreateJobRequest request);
    Task<JobResponse> UpdateAsync(Guid id, UpdateJobRequest request);
    Task DeleteAsync(Guid id);
    Task<JobResponse> ChangeStatusAsync(Guid id, string status);
    Task<List<JobCategoryStatResponse>> GetJobCategoryStatsAsync();
    Task<ImportResult<ImportJobDto>> ImportAsync(IFormFile file);
}

public interface ISkillService
{
    Task<ResultPaginationDto<SkillResponse>> GetAllAsync(string? searchTerm, string? sortBy, bool isDescending, int pageNumber, int pageSize);
    Task<SkillResponse> GetByIdAsync(Guid id);
    Task<SkillResponse> CreateAsync(CreateSkillRequest request);
    Task<SkillResponse> UpdateAsync(Guid id, UpdateSkillRequest request);
    Task DeleteAsync(Guid id);
    Task<ImportResult<CreateSkillRequest>> ImportAsync(IFormFile file);
}

public interface ISavedJobService
{
    Task<ResultPaginationDto<SavedJobResponse>> GetSavedJobsAsync(Guid customerId, int pageNumber, int pageSize);
    Task SaveAsync(Guid jobId, Guid customerId, string? note);
    Task UnsaveAsync(Guid jobId, Guid customerId);
}

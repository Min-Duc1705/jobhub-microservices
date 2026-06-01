using System.Linq.Expressions;
using CommonService.Specifications;
using JobService.Models;
using JobService.Models.Enums;

namespace JobService.Specifications;

/// <summary>Lấy danh sách Job với filter đầy đủ, sort, và phân trang.</summary>
public class JobFilterSpec : BaseSpecification<Job>
{
    public JobFilterSpec(
        string?    searchTerm,
        Guid?      companyId,
        Guid?      customerId,
        string?    location,
        JobLevel?  level,
        JobType?   jobType,
        JobStatus? status,
        double?    salaryMin,
        double?    salaryMax,
        List<Guid>? skillIds,
        string?    sortBy,
        bool       isDescending,
        int        pageNumber,
        int        pageSize)
    {
        AddCriteria(j => !j.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(j => j.Name.ToLower().Contains(term)
                          || (j.Description != null && j.Description.ToLower().Contains(term))
                          || (j.Location != null && j.Location.ToLower().Contains(term)));
        }

        if (companyId.HasValue)
            AddCriteria(j => j.CompanyId == companyId.Value);

        if (customerId.HasValue)
            AddCriteria(j => j.CustomerId == customerId.Value);

        if (!string.IsNullOrWhiteSpace(location))
        {
            var loc = location.ToLower();
            AddCriteria(j => j.Location != null && j.Location.ToLower().Contains(loc));
        }

        if (level.HasValue)
            AddCriteria(j => j.Level == level.Value);

        if (jobType.HasValue)
            AddCriteria(j => j.JobType == jobType.Value);

        if (status.HasValue)
            AddCriteria(j => j.Status == status.Value);
        else if (!customerId.HasValue)  // HR xây filter riêng — không ép PUBLISHED
            AddCriteria(j => j.Status == JobStatus.PUBLISHED);

        if (salaryMin.HasValue)
            AddCriteria(j => j.SalaryMax == null || j.SalaryMax >= salaryMin.Value);

        if (salaryMax.HasValue)
            AddCriteria(j => j.SalaryMin == null || j.SalaryMin <= salaryMax.Value);

        if (skillIds != null && skillIds.Any())
            AddCriteria(j => j.JobSkills.Any(js => skillIds.Contains(js.SkillId)));

        AddInclude(j => j.JobSkills);
        AddInclude("JobSkills.Skill"); // ThenInclude Skill

        var sortMappings = new Dictionary<string, Expression<Func<Job, object>>>
        {
            ["name"]        = j => j.Name,
            ["salary"]      = j => j.SalaryMin!,
            ["viewcount"]   = j => j.ViewCount,
            ["createddate"] = j => j.CreatedDate,
            ["enddate"]     = j => j.EndDate!,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "createddate").ToLower(), j => j.CreatedDate);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng số Job theo bộ filter (không có phân trang).</summary>
public class JobFilterCountSpec : BaseSpecification<Job>
{
    public JobFilterCountSpec(
        string?    searchTerm,
        Guid?      companyId,
        Guid?      customerId,
        string?    location,
        JobLevel?  level,
        JobType?   jobType,
        JobStatus? status,
        double?    salaryMin,
        double?    salaryMax,
        List<Guid>? skillIds)
    {
        AddCriteria(j => !j.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(j => j.Name.ToLower().Contains(term)
                          || (j.Description != null && j.Description.ToLower().Contains(term))
                          || (j.Location != null && j.Location.ToLower().Contains(term)));
        }

        if (companyId.HasValue)
            AddCriteria(j => j.CompanyId == companyId.Value);

        if (customerId.HasValue)
            AddCriteria(j => j.CustomerId == customerId.Value);

        if (!string.IsNullOrWhiteSpace(location))
        {
            var loc = location.ToLower();
            AddCriteria(j => j.Location != null && j.Location.ToLower().Contains(loc));
        }

        if (level.HasValue)    AddCriteria(j => j.Level == level.Value);
        if (jobType.HasValue)  AddCriteria(j => j.JobType == jobType.Value);

        if (status.HasValue)
            AddCriteria(j => j.Status == status.Value);
        else if (!customerId.HasValue)
            AddCriteria(j => j.Status == JobStatus.PUBLISHED);

        if (salaryMin.HasValue)
            AddCriteria(j => j.SalaryMax == null || j.SalaryMax >= salaryMin.Value);

        if (salaryMax.HasValue)
            AddCriteria(j => j.SalaryMin == null || j.SalaryMin <= salaryMax.Value);

        if (skillIds != null && skillIds.Any())
            AddCriteria(j => j.JobSkills.Any(js => skillIds.Contains(js.SkillId)));
    }
}

/// <summary>Lấy Job theo ID, bao gồm danh sách kỹ năng.</summary>
public class JobByIdSpec : BaseSpecification<Job>
{
    public JobByIdSpec(Guid id)
    {
        AddCriteria(j => j.Id == id && !j.IsDeleted);
        AddInclude(j => j.JobSkills);
        AddInclude("JobSkills.Skill"); // ThenInclude Skill
    }
}

// ── Admin specs (không ép PUBLISHED) ──────────────────────────────────────────

/// <summary>
/// Lấy tất cả Job cho Admin (không ép filter Status = PUBLISHED),
/// hỗ trợ filter theo searchTerm, companyId, customerId, status, phân trang.
/// </summary>
public class AdminJobFilterSpec : BaseSpecification<Job>
{
    public AdminJobFilterSpec(
        string?    searchTerm,
        Guid?      companyId,
        Guid?      customerId,
        string?    location,
        JobLevel?  level,
        JobType?   jobType,
        JobStatus? status,
        string?    sortBy,
        bool       isDescending,
        int        pageNumber,
        int        pageSize)
    {
        AddCriteria(j => !j.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(j => j.Name.ToLower().Contains(term)
                          || (j.Description != null && j.Description.ToLower().Contains(term))
                          || (j.Location != null && j.Location.ToLower().Contains(term)));
        }

        if (companyId.HasValue)  AddCriteria(j => j.CompanyId  == companyId.Value);
        if (customerId.HasValue) AddCriteria(j => j.CustomerId == customerId.Value);

        if (!string.IsNullOrWhiteSpace(location))
        {
            var loc = location.ToLower();
            AddCriteria(j => j.Location != null && j.Location.ToLower().Contains(loc));
        }

        if (level.HasValue)   AddCriteria(j => j.Level   == level.Value);
        if (jobType.HasValue) AddCriteria(j => j.JobType == jobType.Value);
        if (status.HasValue)  AddCriteria(j => j.Status  == status.Value);
        // Không ép PUBLISHED — admin thấy tất cả status

        AddInclude(j => j.JobSkills);
        AddInclude("JobSkills.Skill"); // ThenInclude Skill

        var sortMappings = new Dictionary<string, Expression<Func<Job, object>>>
        {
            ["name"]        = j => j.Name,
            ["viewcount"]   = j => j.ViewCount,
            ["createddate"] = j => j.CreatedDate,
            ["enddate"]     = j => j.EndDate!,
        };

        var sortExpr = sortMappings.GetValueOrDefault(
            (sortBy ?? "createddate").ToLower(), j => j.CreatedDate);

        if (isDescending) AddOrderByDescending(sortExpr);
        else              AddOrderBy(sortExpr);

        ApplyPaging((pageNumber - 1) * pageSize, pageSize);
    }
}

/// <summary>Đếm tổng số Job cho Admin (không ép PUBLISHED).</summary>
public class AdminJobCountSpec : BaseSpecification<Job>
{
    public AdminJobCountSpec(
        string?    searchTerm,
        Guid?      companyId,
        Guid?      customerId,
        string?    location,
        JobLevel?  level,
        JobType?   jobType,
        JobStatus? status)
    {
        AddCriteria(j => !j.IsDeleted);

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            var term = searchTerm.ToLower();
            AddCriteria(j => j.Name.ToLower().Contains(term)
                          || (j.Description != null && j.Description.ToLower().Contains(term))
                          || (j.Location != null && j.Location.ToLower().Contains(term)));
        }

        if (companyId.HasValue)  AddCriteria(j => j.CompanyId  == companyId.Value);
        if (customerId.HasValue) AddCriteria(j => j.CustomerId == customerId.Value);

        if (!string.IsNullOrWhiteSpace(location))
        {
            var loc = location.ToLower();
            AddCriteria(j => j.Location != null && j.Location.ToLower().Contains(loc));
        }

        if (level.HasValue)   AddCriteria(j => j.Level   == level.Value);
        if (jobType.HasValue) AddCriteria(j => j.JobType == jobType.Value);
        if (status.HasValue)  AddCriteria(j => j.Status  == status.Value);
        // Không ép PUBLISHED
    }
}

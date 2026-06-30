using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using ResumeService.Models.Request;
using ResumeService.Models.Response;

namespace ResumeService.Services.Interface;

public interface IInterviewService
{
    Task<List<InterviewResponse>> GetByRecruiterAsync(Guid recruiterId);
    Task<List<InterviewResponse>> GetByCandidateAsync(Guid candidateId);
    Task<InterviewResponse> GetByIdAsync(Guid id);
    Task<InterviewResponse> CreateAsync(Guid recruiterId, CreateInterviewRequest request);
    Task<InterviewResponse> UpdateAsync(Guid id, UpdateInterviewRequest request);
    Task DeleteAsync(Guid id);
}

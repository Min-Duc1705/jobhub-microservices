using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using CommonService.Repository;
using ResumeService.Models;

namespace ResumeService.Repositories.Interface;

public interface IInterviewRepository : IGenericRepository<Interview>
{
    Task<List<Interview>> GetByCandidateIdAsync(Guid candidateId);
    Task<List<Interview>> GetByRecruiterIdAsync(Guid recruiterId);
}

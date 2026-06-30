using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using CommonService.Repository;
using Microsoft.EntityFrameworkCore;
using ResumeService.Data;
using ResumeService.Models;
using ResumeService.Repositories.Interface;

namespace ResumeService.Repositories;

public class InterviewRepository : GenericRepository<ResumeDbContext, Interview>, IInterviewRepository
{
    public InterviewRepository(ResumeDbContext context) : base(context) { }

    public async Task<List<Interview>> GetByCandidateIdAsync(Guid candidateId)
    {
        return await _dbSet
            .Where(i => i.CandidateId == candidateId && !i.IsDeleted)
            .OrderByDescending(i => i.InterviewDate)
            .ToListAsync();
    }

    public async Task<List<Interview>> GetByRecruiterIdAsync(Guid recruiterId)
    {
        return await _dbSet
            .Where(i => i.RecruiterId == recruiterId && !i.IsDeleted)
            .OrderByDescending(i => i.InterviewDate)
            .ToListAsync();
    }
}

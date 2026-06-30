using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using AutoMapper;
using CommonService.Exceptions;
using CommonService.Events;
using MassTransit;
using ResumeService.Models;
using ResumeService.Models.Request;
using ResumeService.Models.Response;
using ResumeService.Repositories.Interface;
using ResumeService.Services.Interface;

namespace ResumeService.Services;

public class InterviewServiceImpl : IInterviewService
{
    private readonly IInterviewRepository _interviewRepo;
    private readonly IMapper _mapper;
    private readonly IPublishEndpoint _publishEndpoint;

    public InterviewServiceImpl(IInterviewRepository interviewRepo, IMapper mapper, IPublishEndpoint publishEndpoint)
    {
        _interviewRepo = interviewRepo;
        _mapper = mapper;
        _publishEndpoint = publishEndpoint;
    }

    public async Task<List<InterviewResponse>> GetByRecruiterAsync(Guid recruiterId)
    {
        var list = await _interviewRepo.GetByRecruiterIdAsync(recruiterId);
        return _mapper.Map<List<InterviewResponse>>(list);
    }

    public async Task<List<InterviewResponse>> GetByCandidateAsync(Guid candidateId)
    {
        var list = await _interviewRepo.GetByCandidateIdAsync(candidateId);
        return _mapper.Map<List<InterviewResponse>>(list);
    }

    public async Task<InterviewResponse> GetByIdAsync(Guid id)
    {
        var interview = await _interviewRepo.GetByIdAsync(id);
        if (interview == null || interview.IsDeleted)
            throw new NotFoundException($"Không tìm thấy lịch phỏng vấn với ID: {id}");

        return _mapper.Map<InterviewResponse>(interview);
    }

    public async Task<InterviewResponse> CreateAsync(Guid recruiterId, CreateInterviewRequest request)
    {
        var interview = _mapper.Map<Interview>(request);
        interview.RecruiterId = recruiterId;
        
        // Trạng thái mặc định khi HR tạo thủ công là chờ ứng viên xác nhận
        interview.Status = "PendingConfirm";

        await _interviewRepo.AddAsync(interview);
        await _interviewRepo.SaveChangesAsync();

        var response = _mapper.Map<InterviewResponse>(interview);
        try
        {
            await _publishEndpoint.Publish(new InterviewScheduleChangedEvent
            {
                InterviewId = interview.Id,
                RecruiterId = interview.RecruiterId.ToString(),
                CandidateId = interview.CandidateId.ToString(),
                JobId = interview.JobId.ToString(),
                InterviewDate = interview.InterviewDate,
                Type = interview.Type,
                Status = interview.Status,
                MeetingLink = interview.MeetingLink,
                Notes = interview.Notes,
                Action = "Create"
            });
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MassTransit-Publish] Lỗi gửi event tạo lịch phỏng vấn: {ex.Message}");
        }

        return response;
    }

    public async Task<InterviewResponse> UpdateAsync(Guid id, UpdateInterviewRequest request)
    {
        var interview = await _interviewRepo.GetByIdAsync(id);
        if (interview == null || interview.IsDeleted)
            throw new NotFoundException($"Không tìm thấy lịch phỏng vấn với ID: {id}");

        // Map các thông tin cập nhật (ngày phỏng vấn, link, ghi chú, trạng thái) vào thực thể
        if (request.InterviewDate != default)
            interview.InterviewDate = request.InterviewDate;
            
        if (!string.IsNullOrEmpty(request.Status))
            interview.Status = request.Status;

        if (request.MeetingLink != null)
            interview.MeetingLink = request.MeetingLink;

        if (request.Location != null)
            interview.Location = request.Location;

        if (request.Notes != null)
            interview.Notes = request.Notes;

        _interviewRepo.Update(interview);
        await _interviewRepo.SaveChangesAsync();

        var response = _mapper.Map<InterviewResponse>(interview);
        try
        {
            await _publishEndpoint.Publish(new InterviewScheduleChangedEvent
            {
                InterviewId = interview.Id,
                RecruiterId = interview.RecruiterId.ToString(),
                CandidateId = interview.CandidateId.ToString(),
                JobId = interview.JobId.ToString(),
                InterviewDate = interview.InterviewDate,
                Type = interview.Type,
                Status = interview.Status,
                MeetingLink = interview.MeetingLink,
                Notes = interview.Notes,
                Action = "Update"
            });
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MassTransit-Publish] Lỗi gửi event cập nhật lịch phỏng vấn: {ex.Message}");
        }

        return response;
    }

    public async Task DeleteAsync(Guid id)
    {
        var interview = await _interviewRepo.GetByIdAsync(id);
        if (interview == null || interview.IsDeleted)
            throw new NotFoundException($"Không tìm thấy lịch phỏng vấn với ID: {id}");

        interview.IsDeleted = true;
        interview.DeletedAt = DateTimeOffset.UtcNow;

        _interviewRepo.Update(interview);
        await _interviewRepo.SaveChangesAsync();

        try
        {
            await _publishEndpoint.Publish(new InterviewScheduleChangedEvent
            {
                InterviewId = interview.Id,
                RecruiterId = interview.RecruiterId.ToString(),
                CandidateId = interview.CandidateId.ToString(),
                JobId = interview.JobId.ToString(),
                InterviewDate = interview.InterviewDate,
                Type = interview.Type,
                Status = "Cancelled",
                MeetingLink = interview.MeetingLink,
                Notes = interview.Notes,
                Action = "Delete"
            });
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[MassTransit-Publish] Lỗi gửi event hủy lịch phỏng vấn: {ex.Message}");
        }
    }
}

using CommonService.Events;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Services.Helpers;
using NotificationService.Services.Interface;
using System;
using System.Threading.Tasks;

namespace NotificationService.Consumers;

public class InterviewScheduleChangedConsumer : IConsumer<InterviewScheduleChangedEvent>
{
    private readonly NotificationDbContext _dbContext;
    private readonly IGoogleCalendarService _googleCalendarService;
    private readonly IConfiguration _config;

    public InterviewScheduleChangedConsumer(
        NotificationDbContext dbContext,
        IGoogleCalendarService googleCalendarService,
        IConfiguration config)
    {
        _dbContext = dbContext;
        _googleCalendarService = googleCalendarService;
        _config = config;
    }

    public async Task Consume(ConsumeContext<InterviewScheduleChangedEvent> context)
    {
        var ev = context.Message;
        Console.WriteLine($"[InterviewScheduleChangedConsumer] Nhận event. InterviewId: {ev.InterviewId}, Action: {ev.Action}, Status: {ev.Status}");

        try
        {
            // Kiểm tra xem Recruiter có liên kết Google Calendar không
            var isConnected = await _googleCalendarService.IsConnectedAsync(ev.RecruiterId);
            if (!isConnected)
            {
                Console.WriteLine($"[InterviewScheduleChangedConsumer] Recruiter {ev.RecruiterId} chưa liên kết Google Calendar. Bỏ qua đồng bộ.");
                return;
            }

            var map = await _dbContext.InterviewGoogleEvents.FirstOrDefaultAsync(m => m.InterviewId == ev.InterviewId);

            if (ev.Action == "Delete" || ev.Status == "Cancelled")
            {
                if (map != null)
                {
                    await _googleCalendarService.DeleteEventAsync(ev.RecruiterId, map.GoogleEventId);
                    _dbContext.InterviewGoogleEvents.Remove(map);
                    await _dbContext.SaveChangesAsync();
                    Console.WriteLine($"[InterviewScheduleChangedConsumer] Đã xóa sự kiện Google Calendar ứng với InterviewId: {ev.InterviewId}");
                }
                return;
            }

            // Lấy thông tin ứng viên để lấy Email và Tên hiển thị
            string candidateEmail = "candidate@jobhub.com";
            string candidateName = "Ứng viên";
            try
            {
                var candidateInfo = await UserInfoHelper.GetUserDetailsAsync(ev.CandidateId, _config);
                candidateEmail = candidateInfo.Email ?? candidateEmail;
                candidateName = candidateInfo.FullName ?? candidateName;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[InterviewScheduleChangedConsumer] Lỗi lấy thông tin ứng viên từ ProfileService: {ex.Message}");
            }

            // Lấy thông tin JobName
            string jobName = "Vị trí tuyển dụng";
            // Lấy từ DB hoặc event
            if (!string.IsNullOrEmpty(ev.JobId))
            {
                try
                {
                    // Đọc từ JobService nếu cần thiết, hoặc lấy trực tiếp JobId từ event.
                    // Để đơn giản và nhanh gọn, ta có thể sinh tiêu đề chứa thông tin Vị trí
                }
                catch {}
            }

            var title = $"[JobHub] Lịch phỏng vấn: {candidateName}";
            var notesSection = string.IsNullOrEmpty(ev.Notes) ? "" : $"\nGhi chú: {ev.Notes}";
            var description = $"Lịch hẹn phỏng vấn vòng {ev.Type}.\nTrạng thái: {ev.Status}{notesSection}";
            var start = ev.InterviewDate;
            var end = ev.InterviewDate.AddHours(1); // Thời lượng mặc định 1 tiếng

            if (ev.Action == "Create" || map == null)
            {
                // Nếu là Create hoặc chưa có map (HR liên kết Calendar sau khi lịch đã lên)
                if (map != null)
                {
                    // Tránh tạo trùng
                    await _googleCalendarService.DeleteEventAsync(ev.RecruiterId, map.GoogleEventId);
                    _dbContext.InterviewGoogleEvents.Remove(map);
                    await _dbContext.SaveChangesAsync();
                }

                var googleEventId = await _googleCalendarService.CreateEventAsync(
                    ev.RecruiterId, title, description, start, end, candidateEmail);

                if (!string.IsNullOrEmpty(googleEventId))
                {
                    var newMap = new InterviewGoogleEvent
                    {
                        Id = Guid.NewGuid(),
                        InterviewId = ev.InterviewId,
                        GoogleEventId = googleEventId,
                        RecruiterId = ev.RecruiterId,
                        CreatedAt = DateTimeOffset.UtcNow
                    };
                    await _dbContext.InterviewGoogleEvents.AddAsync(newMap);
                    await _dbContext.SaveChangesAsync();
                    Console.WriteLine($"[InterviewScheduleChangedConsumer] Đã tạo sự kiện Google Calendar thành công cho InterviewId: {ev.InterviewId}. Google EventId: {googleEventId}");
                }
            }
            else if (ev.Action == "Update" && map != null)
            {
                // Cập nhật sự kiện hiện tại
                await _googleCalendarService.UpdateEventAsync(
                    ev.RecruiterId, map.GoogleEventId, title, description, start, end, candidateEmail);
                Console.WriteLine($"[InterviewScheduleChangedConsumer] Đã cập nhật sự kiện Google Calendar ứng với InterviewId: {ev.InterviewId}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[InterviewScheduleChangedConsumer] Lỗi xử lý đồng bộ lịch phỏng vấn: {ex.Message}");
        }
    }
}

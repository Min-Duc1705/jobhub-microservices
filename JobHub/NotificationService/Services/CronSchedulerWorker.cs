using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using NotificationService.Data;
using NotificationService.Models;
using NotificationService.Services.Interface;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Telegram.Bot;

namespace NotificationService.Services;

/// <summary>
/// BackgroundService chạy mỗi 60 giây, kiểm tra các UserCronSchedule đến hạn
/// và thực thi task tương ứng, sau đó gửi kết quả qua Telegram.
/// </summary>
public class CronSchedulerWorker : BackgroundService
{
    private readonly IServiceProvider _serviceProvider;
    private readonly ILogger<CronSchedulerWorker> _logger;
    private readonly TimeSpan _tickInterval = TimeSpan.FromSeconds(60);
    private static readonly HttpClient _http = new HttpClient();

    public CronSchedulerWorker(IServiceProvider serviceProvider, ILogger<CronSchedulerWorker> logger)
    {
        _serviceProvider = serviceProvider;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("[CronSchedulerWorker] Khởi chạy. Tick mỗi 60 giây.");

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await ProcessDueSchedulesAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "[CronSchedulerWorker] Lỗi không mong đợi trong vòng lặp.");
            }

            await Task.Delay(_tickInterval, stoppingToken);
        }
    }

    private async Task ProcessDueSchedulesAsync()
    {
        using var scope = _serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<NotificationDbContext>();
        var config = scope.ServiceProvider.GetRequiredService<IConfiguration>();

        var now = DateTimeOffset.UtcNow;

        // Lấy tất cả schedule đang active và đến hạn
        var dueSchedules = await db.UserCronSchedules
            .Where(s => s.IsActive && s.NextRunAt <= now)
            .ToListAsync();

        if (!dueSchedules.Any()) return;

        _logger.LogInformation("[CronSchedulerWorker] Tìm thấy {Count} schedule đến hạn.", dueSchedules.Count);

        foreach (var schedule in dueSchedules)
        {
            try
            {
                await ExecuteScheduleAsync(schedule, db, config);

                // Cập nhật thời gian chạy
                schedule.LastRunAt = now;
                schedule.NextRunAt = now.AddMinutes(schedule.IntervalMinutes);
                db.UserCronSchedules.Update(schedule);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "[CronSchedulerWorker] Lỗi khi thực thi schedule {Id} (type={Type}).", schedule.Id, schedule.Type);
            }
        }

        await db.SaveChangesAsync();
    }

    private async Task ExecuteScheduleAsync(UserCronSchedule schedule, NotificationDbContext db, IConfiguration config)
    {
        var activeClient = GetBotClient(schedule.BotToken, config);
        if (activeClient == null)
        {
            _logger.LogWarning("[CronSchedulerWorker] Không có BotClient cho schedule {Id}.", schedule.Id);
            return;
        }

        var message = schedule.Type switch
        {
            "jobs"          => await BuildJobsMessageAsync(schedule, config),
            "notifications" => await BuildNotificationsMessageAsync(schedule, db),
            "applications"  => await BuildApplicationsMessageAsync(schedule, config),
            "interviews"    => await BuildInterviewsMessageAsync(schedule, db),
            "campaigns"     => await BuildCampaignsMessageAsync(schedule, db),
            _               => null
        };

        if (string.IsNullOrEmpty(message)) return;

        try
        {
            await activeClient.SendTextMessageAsync(
                schedule.TelegramChatId,
                message,
                parseMode: Telegram.Bot.Types.Enums.ParseMode.Html);
        }
        catch
        {
            // Fallback: gửi plain text
            var plain = System.Text.RegularExpressions.Regex.Replace(message, "<[^>]+>", "");
            await activeClient.SendTextMessageAsync(schedule.TelegramChatId, plain);
        }
    }

    // ── Job Notifications ──────────────────────────────────────────────────────

    private async Task<string?> BuildJobsMessageAsync(UserCronSchedule schedule, IConfiguration config)
    {
        try
        {
            var token = GenerateInternalToken(config);
            var since = schedule.LastRunAt ?? DateTimeOffset.UtcNow.AddMinutes(-schedule.IntervalMinutes);

            var url = string.IsNullOrEmpty(schedule.Keyword)
                ? $"http://jobservice:8080/api/v1/jobs?pageSize=5&status=PUBLISHED&sortBy=createdAt&sortDirection=desc"
                : $"http://jobservice:8080/api/v1/jobs?keyword={Uri.EscapeDataString(schedule.Keyword)}&pageSize=5&status=PUBLISHED&sortBy=createdAt&sortDirection=desc";

            var req = new HttpRequestMessage(HttpMethod.Get, url);
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var res = await _http.SendAsync(req);

            if (!res.IsSuccessStatusCode) return null;

            var json = await res.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(json);
            var result = doc.RootElement.GetProperty("data").GetProperty("result");

            if (result.ValueKind != JsonValueKind.Array || result.GetArrayLength() == 0)
            {
                return $"🔍 <b>Thông báo việc làm tự động</b>\n\n" +
                       $"Không có việc làm mới{(string.IsNullOrEmpty(schedule.Keyword) ? "" : $" theo keyword \"<b>{schedule.Keyword}</b>\"")} trong {schedule.IntervalMinutes} phút vừa qua.";
            }

            // Lọc job mới hơn lastRunAt
            var jobs = result.EnumerateArray()
                .Where(j =>
                {
                    if (j.TryGetProperty("createdAt", out var caProp) && caProp.ValueKind == JsonValueKind.String)
                    {
                        if (DateTimeOffset.TryParse(caProp.GetString(), out var ca))
                            return ca >= since;
                    }
                    return true; // nếu không có createdAt thì vẫn hiển thị
                })
                .ToList();

            if (!jobs.Any())
            {
                return $"🔍 <b>Thông báo việc làm tự động</b>\n\n" +
                       $"Không có việc làm mới{(string.IsNullOrEmpty(schedule.Keyword) ? "" : $" theo keyword \"<b>{schedule.Keyword}</b>\"")} trong {FormatInterval(schedule.IntervalMinutes)} vừa qua.";
            }

            var sb = new StringBuilder();
            var keywordText = string.IsNullOrEmpty(schedule.Keyword) ? "mới nhất" : $"\"<b>{schedule.Keyword}</b>\"";
            sb.AppendLine($"🔔 <b>Việc làm {keywordText} — {jobs.Count} tin mới</b>\n");

            foreach (var job in jobs.Take(5))
            {
                var name     = job.TryGetProperty("name",     out var np) ? np.GetString() : "N/A";
                var company  = job.TryGetProperty("company",  out var cp) && cp.TryGetProperty("name", out var cnp) ? cnp.GetString() : "N/A";
                var location = job.TryGetProperty("location", out var lp) && lp.ValueKind != JsonValueKind.Null ? lp.GetString() : "N/A";
                var id       = job.TryGetProperty("id",       out var ip) ? ip.GetString() : null;

                var salaryMin = job.TryGetProperty("salaryMin", out var smin) && smin.ValueKind == JsonValueKind.Number ? smin.GetDouble() : (double?)null;
                var salaryMax = job.TryGetProperty("salaryMax", out var smax) && smax.ValueKind == JsonValueKind.Number ? smax.GetDouble() : (double?)null;
                var isNego   = job.TryGetProperty("isSalaryNegotiable", out var neg) && neg.GetBoolean();
                var salary   = isNego || (!salaryMin.HasValue && !salaryMax.HasValue)
                    ? "Thỏa thuận"
                    : $"{salaryMin?.ToString("N0") ?? "0"} – {salaryMax?.ToString("N0") ?? "N/A"} VND";

                var domain = config["FrontendUrl"]?.TrimEnd('/') ?? "https://jobhub-frontend-two.vercel.app";
                var link   = id != null ? $"{domain}/jobs/{id}" : domain;

                sb.AppendLine($"💼 <b><a href=\"{link}\">{name}</a></b>");
                sb.AppendLine($"   🏢 {company}  📍 {location}");
                sb.AppendLine($"   💰 {salary}");
                sb.AppendLine();
            }

            sb.AppendLine($"⏰ <i>Lịch: mỗi {FormatInterval(schedule.IntervalMinutes)} | ID #{schedule.Id} | /pause {schedule.Id} để tạm dừng</i>");
            return sb.ToString();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "[CronSchedulerWorker] BuildJobsMessage error schedule {Id}", schedule.Id);
            return null;
        }
    }

    // ── Notifications ──────────────────────────────────────────────────────────

    private async Task<string?> BuildNotificationsMessageAsync(UserCronSchedule schedule, NotificationDbContext db)
    {
        var since = schedule.LastRunAt ?? DateTimeOffset.UtcNow.AddMinutes(-schedule.IntervalMinutes);

        var notifs = await db.Notifications
            .Where(n => n.AppUserId == schedule.UserId && !n.IsRead && n.CreatedDate >= since)
            .OrderByDescending(n => n.CreatedDate)
            .Take(5)
            .ToListAsync();

        if (!notifs.Any()) return null; // Không gửi nếu không có gì mới

        var sb = new StringBuilder();
        sb.AppendLine($"🔔 <b>Thông báo chưa đọc — {notifs.Count} mới</b>\n");

        foreach (var n in notifs)
        {
            sb.AppendLine($"✉️ <b>{n.Title}</b>");
            sb.AppendLine($"   {n.Message}");
            sb.AppendLine($"   <i>{n.CreatedDate:dd/MM HH:mm}</i>\n");
        }

        sb.AppendLine($"⏰ <i>Lịch: mỗi {FormatInterval(schedule.IntervalMinutes)} | /pause {schedule.Id} để tạm dừng</i>");
        return sb.ToString();
    }

    // ── Applications (HR) ─────────────────────────────────────────────────────

    private async Task<string?> BuildApplicationsMessageAsync(UserCronSchedule schedule, IConfiguration config)
    {
        try
        {
            var token = GenerateInternalToken(config);
            var since = schedule.LastRunAt ?? DateTimeOffset.UtcNow.AddMinutes(-schedule.IntervalMinutes);

            // Gọi JobService để lấy jobs của HR này, sau đó lấy applications cho từng job
            var jobReq = new HttpRequestMessage(HttpMethod.Get,
                $"http://jobservice:8080/api/v1/jobs?CustomerId={schedule.UserId}&pageSize=5&status=PUBLISHED");
            jobReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            var jobRes = await _http.SendAsync(jobReq);
            if (!jobRes.IsSuccessStatusCode) return null;

            var jobJson = await jobRes.Content.ReadAsStringAsync();
            using var jobDoc = JsonDocument.Parse(jobJson);
            var jobs = jobDoc.RootElement.GetProperty("data").GetProperty("result");

            int totalNew = 0;
            var sb = new StringBuilder();
            sb.AppendLine($"👥 <b>Ứng viên mới — {FormatInterval(schedule.IntervalMinutes)} vừa qua</b>\n");

            foreach (var job in jobs.EnumerateArray().Take(3))
            {
                var jobId   = job.TryGetProperty("id",   out var idProp) ? idProp.GetString() : null;
                var jobName = job.TryGetProperty("name", out var nameProp) ? nameProp.GetString() : "N/A";
                if (jobId == null) continue;

                var appReq = new HttpRequestMessage(HttpMethod.Get,
                    $"http://jobservice:8080/api/v1/applications?jobId={jobId}&pageSize=100&sortBy=createdAt&sortDirection=desc");
                appReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                var appRes = await _http.SendAsync(appReq);
                if (!appRes.IsSuccessStatusCode) continue;

                var appJson = await appRes.Content.ReadAsStringAsync();
                using var appDoc = JsonDocument.Parse(appJson);
                var apps = appDoc.RootElement.GetProperty("data").GetProperty("result");

                var newApps = apps.EnumerateArray()
                    .Where(a =>
                    {
                        if (a.TryGetProperty("createdAt", out var ca) && DateTimeOffset.TryParse(ca.GetString(), out var dt))
                            return dt >= since;
                        return false;
                    })
                    .Take(3)
                    .ToList();

                if (!newApps.Any()) continue;
                totalNew += newApps.Count;

                sb.AppendLine($"💼 <b>{jobName}</b> — {newApps.Count} ứng viên mới");
                var domain = config["FrontendUrl"]?.TrimEnd('/') ?? "https://jobhub-frontend-two.vercel.app";
                sb.AppendLine($"   👉 <a href=\"{domain}/hr/jobs/{jobId}/applications\">Xem danh sách ứng viên</a>\n");
            }

            if (totalNew == 0) return null;

            sb.AppendLine($"⏰ <i>Lịch: mỗi {FormatInterval(schedule.IntervalMinutes)} | /pause {schedule.Id} để tạm dừng</i>");
            return sb.ToString();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "[CronSchedulerWorker] BuildApplicationsMessage error schedule {Id}", schedule.Id);
            return null;
        }
    }

    // ── Interviews (Candidate) ─────────────────────────────────────────────────

    private async Task<string?> BuildInterviewsMessageAsync(UserCronSchedule schedule, NotificationDbContext db)
    {
        var since = schedule.LastRunAt ?? DateTimeOffset.UtcNow.AddMinutes(-schedule.IntervalMinutes);

        var list = await (from conv in db.HireAgentConversations
                          join camp in db.HireAgentCampaigns on conv.CampaignId equals camp.Id
                          where conv.CandidateId == schedule.UserId.ToString()
                                && conv.CreatedAt >= since
                          orderby conv.CreatedAt descending
                          select new { conv.Status, conv.InterviewDate, conv.MatchingScore, camp.JobName })
            .Take(5)
            .ToListAsync();

        if (!list.Any()) return null;

        var sb = new StringBuilder();
        sb.AppendLine($"📅 <b>Cập nhật phỏng vấn AI — {list.Count} mới</b>\n");

        foreach (var item in list)
        {
            var dateStr = item.InterviewDate.HasValue
                ? item.InterviewDate.Value.ToString("dd/MM/yyyy HH:mm")
                : "Chưa lên lịch";
            sb.AppendLine($"💼 <b>{item.JobName}</b>");
            sb.AppendLine($"   Trạng thái: {item.Status}  |  Lịch hẹn: {dateStr}  |  Match: {item.MatchingScore}%\n");
        }

        sb.AppendLine($"⏰ <i>Lịch: mỗi {FormatInterval(schedule.IntervalMinutes)} | /pause {schedule.Id} để tạm dừng</i>");
        return sb.ToString();
    }

    // ── Campaigns (HR) ────────────────────────────────────────────────────────

    private async Task<string?> BuildCampaignsMessageAsync(UserCronSchedule schedule, NotificationDbContext db)
    {
        var campaigns = await db.HireAgentCampaigns
            .Where(c => c.RecruiterId == schedule.UserId.ToString() && c.Status == "Active")
            .OrderByDescending(c => c.CreatedAt)
            .Take(5)
            .ToListAsync();

        if (!campaigns.Any()) return null;

        var sb = new StringBuilder();
        sb.AppendLine($"🤖 <b>Tiến độ chiến dịch AI — {campaigns.Count} đang chạy</b>\n");

        foreach (var c in campaigns)
        {
            sb.AppendLine($"💼 <b>{c.JobName}</b>");
            sb.AppendLine($"   Mục tiêu: {c.TargetCount} ứng viên  |  Địa điểm: {c.JobLocation ?? "N/A"}\n");
        }

        sb.AppendLine($"⏰ <i>Lịch: mỗi {FormatInterval(schedule.IntervalMinutes)} | /pause {schedule.Id} để tạm dừng</i>");
        return sb.ToString();
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static TelegramBotClient? GetBotClient(string? botToken, IConfiguration config)
    {
        var token = !string.IsNullOrEmpty(botToken)
            ? botToken
            : config["Telegram:BotToken"];

        if (string.IsNullOrEmpty(token) || token == "YOUR_TELEGRAM_BOT_TOKEN") return null;
        return new TelegramBotClient(token);
    }

    private static string GenerateInternalToken(IConfiguration config)
    {
        var secretKey = config["Jwt:SecretKey"] ?? "JobHubSuperSecretKeyMinimum64CharactersLongToSupportHS512Algorithm!!";
        var issuer    = config["Jwt:Issuer"]    ?? "JobHub";
        var audience  = config["Jwt:Audience"]  ?? "JobHubClient";
        return InternalTokenGenerator.GenerateInternalToken(secretKey, issuer, audience);
    }

    public static string FormatInterval(int minutes) => minutes switch
    {
        < 60  => $"{minutes} phút",
        60    => "1 giờ",
        120   => "2 giờ",
        240   => "4 giờ",
        360   => "6 giờ",
        720   => "12 giờ",
        1440  => "24 giờ",
        _     => $"{minutes / 60} giờ"
    };
}

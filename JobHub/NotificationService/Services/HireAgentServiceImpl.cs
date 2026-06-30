using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Configuration;
using NotificationService.Data;
using NotificationService.Hubs;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Interface;
using System;
using System.Collections.Concurrent;
using System.Net.Http;

namespace NotificationService.Services;

/// <summary>
/// HireAgent Service — tách thành các partial class theo trách nhiệm:
/// <list type="bullet">
///   <item><see cref="HireAgentServiceImpl.Campaign.cs"/> — quản lý chiến dịch tuyển dụng &amp; outreach</item>
///   <item><see cref="HireAgentServiceImpl.Interview.cs"/> — phỏng vấn sàng lọc, đặt lịch, xác nhận lịch</item>
///   <item><see cref="Helpers/UserInfoHelper.cs"/> — truy vấn thông tin user từ microservice</item>
///   <item><see cref="Helpers/LocationHelper.cs"/> — normalize &amp; so khớp địa điểm</item>
/// </list>
/// </summary>
public partial class HireAgentServiceImpl : IHireAgentService
{
    // ── Shared dependencies ──────────────────────────────────────────────────
    private readonly IHireAgentRepository       _hireAgentRepo;
    private readonly IChatRepository            _chatRepo;
    private readonly IChatService               _chatService;
    private readonly IHubContext<ChatHub>        _hubContext;
    private readonly IConfiguration             _config;
    private readonly IServiceScopeFactory       _scopeFactory;
    private readonly IGoogleCalendarService     _googleCalendarService;
    private readonly NotificationDbContext      _dbContext;

    // ── Shared statics ───────────────────────────────────────────────────────
    private static readonly HttpClient _httpClient = new HttpClient { Timeout = TimeSpan.FromMinutes(10) };

    /// <summary>Ngăn chạy song song cùng một chiến dịch (CampaignId → running flag).</summary>
    private static readonly ConcurrentDictionary<Guid, bool> _runningCampaigns = new();

    public HireAgentServiceImpl(
        IHireAgentRepository hireAgentRepo,
        IChatRepository chatRepo,
        IChatService chatService,
        IHubContext<ChatHub> hubContext,
        IConfiguration config,
        IServiceScopeFactory scopeFactory,
        IGoogleCalendarService googleCalendarService,
        NotificationDbContext dbContext)
    {
        _hireAgentRepo = hireAgentRepo;
        _chatRepo      = chatRepo;
        _chatService   = chatService;
        _hubContext    = hubContext;
        _config        = config;
        _scopeFactory  = scopeFactory;
        _googleCalendarService = googleCalendarService;
        _dbContext     = dbContext;
    }
}

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using NotificationService.Repositories.Interface;
using NotificationService.Services.Interface;
using System;
using System.Threading;
using System.Threading.Tasks;

namespace NotificationService.Services;

public class HireAgentWorker : BackgroundService
{
    private readonly IServiceProvider _serviceProvider;
    private readonly TimeSpan _period = TimeSpan.FromMinutes(5);

    public HireAgentWorker(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        Console.WriteLine("[HireAgentWorker] Khởi chạy worker chạy ngầm.");
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                using (var scope = _serviceProvider.CreateScope())
                {
                    var hireAgentRepo = scope.ServiceProvider.GetRequiredService<IHireAgentRepository>();
                    var hireAgentService = scope.ServiceProvider.GetRequiredService<IHireAgentService>();

                    var activeCampaigns = await hireAgentRepo.GetActiveCampaignsAsync();
                    foreach (var campaign in activeCampaigns)
                    {
                        Console.WriteLine($"[HireAgentWorker] Đang chạy quét tiếp cận cho campaign {campaign.Id} (Job: {campaign.JobName})");
                        await hireAgentService.RunCampaignOutreachAsync(campaign.Id);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[HireAgentWorker] Lỗi khi chạy quét chu kỳ: {ex.Message}");
            }

            await Task.Delay(_period, stoppingToken);
        }
    }
}

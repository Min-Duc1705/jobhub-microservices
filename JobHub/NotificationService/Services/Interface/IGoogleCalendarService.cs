using System;
using System.Threading.Tasks;
using NotificationService.Models;

namespace NotificationService.Services.Interface;

public interface IGoogleCalendarService
{
    string GetAuthUrl(string userId);
    Task<UserGoogleCredential> ExchangeCodeForTokensAsync(string userId, string code);
    Task<bool> IsConnectedAsync(string userId);
    Task<string> GetConnectedEmailAsync(string userId);
    Task DisconnectAsync(string userId);
    
    // Core event creation & sync APIs
    Task<string?> CreateEventAsync(
        string recruiterId, 
        string title, 
        string description, 
        DateTimeOffset start, 
        DateTimeOffset end, 
        string candidateEmail);
        
    Task UpdateEventAsync(
        string recruiterId, 
        string eventId, 
        string title, 
        string description, 
        DateTimeOffset start, 
        DateTimeOffset end, 
        string candidateEmail);
        
    Task DeleteEventAsync(string recruiterId, string eventId);
    Task SyncAllExistingInterviewsAsync(string recruiterId);
}

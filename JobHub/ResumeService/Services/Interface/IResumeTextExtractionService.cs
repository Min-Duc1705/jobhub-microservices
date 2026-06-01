using Microsoft.AspNetCore.Http;

namespace ResumeService.Services.Interface;

public interface IResumeTextExtractionService
{
    Task<string> ExtractAsync(IFormFile file, CancellationToken cancellationToken = default);
    Task<string> ExtractAsync(Stream stream, string fileName, CancellationToken cancellationToken = default);
}

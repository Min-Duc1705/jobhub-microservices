using System.Text;
using System.Text.RegularExpressions;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using Microsoft.AspNetCore.Http;
using ResumeService.Services.Interface;
using UglyToad.PdfPig;

namespace ResumeService.Services;

public class ResumeTextExtractionService : IResumeTextExtractionService
{
    private const int MaxExtractedChars = 60_000;

    public async Task<string> ExtractAsync(IFormFile file, CancellationToken cancellationToken = default)
    {
        await using var stream = file.OpenReadStream();
        return await ExtractAsync(stream, file.FileName, cancellationToken);
    }

    public async Task<string> ExtractAsync(Stream stream, string fileName, CancellationToken cancellationToken = default)
    {
        if (stream.CanSeek) stream.Position = 0;

        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        var rawText = extension switch
        {
            ".pdf" => ExtractPdf(stream),
            ".docx" => ExtractDocx(stream),
            ".doc" => ExtractDoc(stream),
            _ => await ExtractPlainTextAsync(stream, cancellationToken),
        };

        return Normalize(rawText);
    }

    private static string ExtractPdf(Stream stream)
    {
        string text = string.Empty;
        try
        {
            using var document = PdfDocument.Open(stream);
            var builder = new StringBuilder();

            foreach (var page in document.GetPages())
            {
                builder.AppendLine(page.Text);
                if (builder.Length >= MaxExtractedChars) break;
            }

            text = builder.ToString();
        }
        catch (Exception)
        {
            // Bỏ qua để thử fallback bằng SautinSoft bên dưới
        }

        // Fallback sang SautinSoft.Document nếu PdfPig trả về rỗng hoặc bị lỗi
        if (string.IsNullOrWhiteSpace(text))
        {
            try
            {
                if (stream.CanSeek) stream.Position = 0;
                var loadOptions = new SautinSoft.Document.PdfLoadOptions();
                var doc = SautinSoft.Document.DocumentCore.Load(stream, loadOptions);
                text = doc.Content.ToString() ?? string.Empty;
            }
            catch (Exception ex)
            {
                throw new InvalidDataException("Không thể đọc file định dạng .pdf (file có thể bị mã hóa, có mật khẩu hoặc lỗi cấu trúc).", ex);
            }
        }

        return text;
    }

    private static string ExtractDocx(Stream stream)
    {
        try
        {
            using var document = WordprocessingDocument.Open(stream, false);
            var body = document.MainDocumentPart?.Document.Body;
            if (body == null) return string.Empty;

            var builder = new StringBuilder();
            foreach (var paragraph in body.Descendants<Paragraph>())
            {
                var text = string.Join(" ", paragraph.Descendants<Text>().Select(t => t.Text));
                if (!string.IsNullOrWhiteSpace(text))
                    builder.AppendLine(text);

                if (builder.Length >= MaxExtractedChars) break;
            }

            return builder.ToString();
        }
        catch (Exception ex)
        {
            // Fallback: có thể file thực chất là .doc nhưng bị đổi tên thành .docx
            try
            {
                if (stream.CanSeek) stream.Position = 0;
                return ExtractDoc(stream);
            }
            catch
            {
                throw new InvalidDataException("Không thể đọc file định dạng .docx (file có thể bị lỗi cấu trúc hoặc sai định dạng thực tế).", ex);
            }
        }
    }

    private static string ExtractDoc(Stream stream)
    {
        try
        {
            var loadOptions = new SautinSoft.Document.DocLoadOptions();
            var doc = SautinSoft.Document.DocumentCore.Load(stream, loadOptions);
            return doc.Content.ToString() ?? string.Empty;
        }
        catch (Exception ex)
        {
            // Fallback: có thể file thực chất là .docx nhưng bị đổi tên thành .doc
            try
            {
                if (stream.CanSeek) stream.Position = 0;
                return ExtractDocx(stream);
            }
            catch
            {
                throw new InvalidDataException("Không thể đọc file định dạng .doc (file có thể bị lỗi cấu trúc hoặc sai định dạng thực tế).", ex);
            }
        }
    }

    private static async Task<string> ExtractPlainTextAsync(Stream stream, CancellationToken cancellationToken)
    {
        using var reader = new StreamReader(stream, Encoding.UTF8, detectEncodingFromByteOrderMarks: true, leaveOpen: true);
        var buffer = new char[MaxExtractedChars];
        var read = await reader.ReadBlockAsync(buffer.AsMemory(0, buffer.Length), cancellationToken);
        return new string(buffer, 0, read);
    }

    private static string Normalize(string value)
    {
        if (string.IsNullOrWhiteSpace(value)) return string.Empty;

        // Loại bỏ ký tự null byte \0 để tránh lỗi PostgreSQL UTF-8 encoding
        var cleanValue = value.Replace("\0", string.Empty);

        var normalized = Regex.Replace(cleanValue, @"[ \t\r\f\v]+", " ");
        normalized = Regex.Replace(normalized, @"\n{3,}", "\n\n");
        normalized = normalized.Trim();

        return normalized.Length <= MaxExtractedChars
            ? normalized
            : normalized[..MaxExtractedChars];
    }
}

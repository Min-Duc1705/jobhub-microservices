using Microsoft.AspNetCore.Http;
using System.IO;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace CommonService.Import;

public class ValidationError
{
    public int RowIndex { get; set; }
    public string ColumnName { get; set; } = string.Empty;
    public string ErrorMessage { get; set; } = string.Empty;
}

public class ImportResult<T>
{
    public List<T> Data { get; set; } = new();
    public List<ValidationError> Errors { get; set; } = new();
    public bool IsSuccess => Errors.Count == 0;
}

public interface IExcelCsvImportService
{
    /// <summary>
    /// Parses an Excel (.xlsx) or CSV (.csv) file stream into a list of generic DTOs, performs model validation, and returns results.
    /// </summary>
    Task<ImportResult<T>> ImportAsync<T>(Stream stream, string fileExtension) where T : class, new();

    /// <summary>
    /// Overload that directly accepts IFormFile.
    /// </summary>
    Task<ImportResult<T>> ImportAsync<T>(IFormFile file) where T : class, new();
}

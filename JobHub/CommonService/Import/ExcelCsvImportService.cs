using Microsoft.AspNetCore.Http;
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using MiniExcelLibs;

namespace CommonService.Import;

public class ExcelCsvImportService : IExcelCsvImportService
{
    public async Task<ImportResult<T>> ImportAsync<T>(Stream stream, string fileExtension) where T : class, new()
    {
        var result = new ImportResult<T>();

        if (stream == null || stream.Length == 0)
        {
            result.Errors.Add(new ValidationError
            {
                RowIndex = 0,
                ErrorMessage = "File stream rỗng hoặc không hợp lệ."
            });
            return result;
        }

        ExcelType excelType;
        var ext = fileExtension.TrimStart('.').ToLower();
        if (ext == "xlsx")
        {
            excelType = ExcelType.XLSX;
        }
        else if (ext == "csv")
        {
            excelType = ExcelType.CSV;
        }
        else
        {
            result.Errors.Add(new ValidationError
            {
                RowIndex = 0,
                ErrorMessage = $"Định dạng file không được hỗ trợ: {fileExtension}. Chỉ hỗ trợ .xlsx và .csv"
            });
            return result;
        }

        try
        {
            if (stream.CanSeek)
            {
                stream.Position = 0;
            }

            // Đọc dữ liệu bằng MiniExcel
            var rows = MiniExcel.Query<T>(stream, excelType: excelType).ToList();

            if (rows == null || rows.Count == 0)
            {
                result.Errors.Add(new ValidationError
                {
                    RowIndex = 0,
                    ErrorMessage = "Không tìm thấy dữ liệu trong file."
                });
                return result;
            }

            // Validate từng dòng sử dụng DataAnnotations
            for (int i = 0; i < rows.Count; i++)
            {
                var row = rows[i];
                var rowIndex = i + 2; // Dòng 1 là tiêu đề, dữ liệu bắt đầu từ dòng 2

                if (row == null)
                {
                    result.Errors.Add(new ValidationError
                    {
                        RowIndex = rowIndex,
                        ErrorMessage = "Dòng dữ liệu bị null."
                    });
                    continue;
                }

                var validationContext = new ValidationContext(row);
                var validationResults = new List<ValidationResult>();

                if (Validator.TryValidateObject(row, validationContext, validationResults, true))
                {
                    result.Data.Add(row);
                }
                else
                {
                    foreach (var valResult in validationResults)
                    {
                        result.Errors.Add(new ValidationError
                        {
                            RowIndex = rowIndex,
                            ColumnName = string.Join(", ", valResult.MemberNames),
                            ErrorMessage = valResult.ErrorMessage ?? "Giá trị không hợp lệ."
                        });
                    }
                }
            }
        }
        catch (Exception ex)
        {
            result.Errors.Add(new ValidationError
            {
                RowIndex = 0,
                ErrorMessage = $"Lỗi khi đọc file: {ex.Message}"
            });
        }

        return result;
    }

    public async Task<ImportResult<T>> ImportAsync<T>(IFormFile file) where T : class, new()
    {
        if (file == null || file.Length == 0)
        {
            var result = new ImportResult<T>();
            result.Errors.Add(new ValidationError
            {
                RowIndex = 0,
                ErrorMessage = "File upload bị rỗng hoặc null."
            });
            return result;
        }

        var fileExtension = Path.GetExtension(file.FileName);
        using var stream = file.OpenReadStream();
        return await ImportAsync<T>(stream, fileExtension);
    }
}

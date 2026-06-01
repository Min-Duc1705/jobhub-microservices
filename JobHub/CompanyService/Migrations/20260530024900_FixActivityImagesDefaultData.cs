using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CompanyService.Migrations
{
    /// <inheritdoc />
    public partial class FixActivityImagesDefaultData : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Sửa các row cũ có giá trị ActivityImages không hợp lệ
            // (chuỗi rỗng "" hoặc object {} thay vì array [])
            migrationBuilder.Sql(
                "UPDATE \"Companies\" " +
                "SET \"ActivityImages\" = '[]'::jsonb " +
                "WHERE \"ActivityImages\"::text IN ('\"\"', '{}') " +
                "   OR \"ActivityImages\" IS NULL;");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            // Không cần rollback data
        }
    }
}

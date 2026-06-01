using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CompanyService.Migrations
{
    /// <inheritdoc />
    public partial class AddActivityImages : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ActivityImages",
                table: "Companies",
                type: "jsonb",
                nullable: false,
                defaultValue: "[]");

            // Sửa các row cũ có giá trị không hợp lệ (chuỗi rỗng / {} / null)
            migrationBuilder.Sql(
                "UPDATE \"Companies\" SET \"ActivityImages\" = '[]'::jsonb " +
                "WHERE \"ActivityImages\" IS NULL " +
                "   OR \"ActivityImages\"::text = '\"\"' " +
                "   OR \"ActivityImages\"::text = '{}'");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ActivityImages",
                table: "Companies");
        }
    }
}

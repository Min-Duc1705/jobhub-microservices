using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace JobService.Migrations
{
    /// <inheritdoc />
    public partial class AddRequirementsToJob : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Requirements",
                table: "Jobs",
                type: "text",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Requirements",
                table: "Jobs");
        }
    }
}

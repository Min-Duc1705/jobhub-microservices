using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AuthService.Migrations
{
    /// <inheritdoc />
    public partial class AddIndexes : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateIndex(
                name: "IX_Roles_IsDeleted",
                table: "Roles",
                column: "IsDeleted");

            migrationBuilder.CreateIndex(
                name: "IX_Permissions_Module",
                table: "Permissions",
                column: "Module");

            migrationBuilder.CreateIndex(
                name: "IX_Users_IsDeleted",
                table: "AppUsers",
                column: "IsDeleted");

            migrationBuilder.CreateIndex(
                name: "IX_Users_Status",
                table: "AppUsers",
                column: "Status");

            migrationBuilder.CreateIndex(
                name: "IX_Users_Username",
                table: "AppUsers",
                column: "Username");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_Roles_IsDeleted",
                table: "Roles");

            migrationBuilder.DropIndex(
                name: "IX_Permissions_Module",
                table: "Permissions");

            migrationBuilder.DropIndex(
                name: "IX_Users_IsDeleted",
                table: "AppUsers");

            migrationBuilder.DropIndex(
                name: "IX_Users_Status",
                table: "AppUsers");

            migrationBuilder.DropIndex(
                name: "IX_Users_Username",
                table: "AppUsers");
        }
    }
}

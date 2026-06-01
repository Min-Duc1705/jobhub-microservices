using System.Text;
using CommonService.Exceptions;
using CommonService.Extensions;
using CommonService.Filters;
using CompanyService.Data;
using CompanyService.Repositories;
using CompanyService.Repositories.Interface;
using CompanyService.Services;
using CompanyService.Services.Interface;
using CompanyService.Validators;
using FluentValidation;
using FluentValidation.AspNetCore;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

// ── Database (PostgreSQL) ──────────────────────────────────────────────────────
builder.Services.AddDbContext<CompanyDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("CompanyDb")));

// ── Redis Cache (dùng chung namespace với Auth để đọc permissions) ─────────────
builder.Services.AddCommonRedisCache(builder.Configuration, "JobHubAuth_");

// ── Repositories ──────────────────────────────────────────────────────────────
builder.Services.AddScoped<ICompanyRepository, CompanyRepository>();

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<ICompanyService, CompanyServiceImpl>();

// ── AutoMapper ────────────────────────────────────────────────────────────────
builder.Services.AddAutoMapper(cfg =>
    cfg.AddMaps(typeof(CompanyService.Mapping.CompanyMappingProfile).Assembly));

// ── Exception Handler ─────────────────────────────────────────────────────────
builder.Services.AddCommonApiServices();

// ── MinIO Storage ─────────────────────────────────────────────────────────────
builder.Services.AddMinioStorage(builder.Configuration);
builder.Services.AddFileService();

// ── Controllers + Filters ─────────────────────────────────────────────────────
// FluentValidation v11: tách biệt khỏi AddControllers
builder.Services.AddFluentValidationAutoValidation();
builder.Services.AddValidatorsFromAssemblyContaining<CreateCompanyRequestValidator>();

builder.Services.AddControllers(options =>
{
    options.Filters.Add<FormatResponseFilter>();
    options.Filters.Add<PermissionInterceptor>();
})
.AddJsonOptions(options =>
{
    // Cho phép deserialize enum từ string ("STARTUP", "SME", "ENTERPRISE")
    // thay vì chỉ chấp nhận số nguyên (0, 1, 2)
    options.JsonSerializerOptions.Converters.Add(
        new System.Text.Json.Serialization.JsonStringEnumConverter());
});

// ── JWT Authentication ─────────────────────────────────────────────────────────
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer           = true,
            ValidateAudience         = true,
            ValidateLifetime         = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer              = builder.Configuration["Jwt:Issuer"],
            ValidAudience            = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey         = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:SecretKey"]!)),
            ClockSkew = TimeSpan.Zero
        };
    });

builder.Services.AddAuthorization();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// ── Build & Pipeline ───────────────────────────────────────────────────────────
var app = builder.Build();

app.UseCommonErrorHandling("CompanyService");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

// ── Auto-migrate DB khi khởi động ─────────────────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<CompanyDbContext>();
    await db.Database.MigrateAsync();
    await CompanyService.Data.SeedData.CompanySeeder.SeedAsync(db);
}

app.Run();

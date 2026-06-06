using System.Text;
using CommonService.Extensions;
using CommonService.Filters;
using FluentValidation;
using FluentValidation.AspNetCore;
using ResumeService.Data;
using ResumeService.Repositories;
using ResumeService.Repositories.Interface;
using ResumeService.Services;
using ResumeService.Services.Interface;
using ResumeService.Validators;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using MassTransit;
using ResumeService.Consumers;

var builder = WebApplication.CreateBuilder(args);

// ── Database (PostgreSQL) ──────────────────────────────────────────────────────
builder.Services.AddDbContext<ResumeDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("ResumeDb")));

// ── Redis Cache (đọc permissions từ Auth namespace) ────────────────────────────
builder.Services.AddCommonRedisCache(builder.Configuration, "JobHubAuth_");

// ── Repositories ──────────────────────────────────────────────────────────────
builder.Services.AddScoped<IResumeRepository,      ResumeRepository>();
builder.Services.AddScoped<IApplicationRepository, ApplicationRepository>();

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<IResumeService,      ResumeServiceImpl>();
builder.Services.AddScoped<IApplicationService, ApplicationServiceImpl>();
builder.Services.AddScoped<IResumeTextExtractionService, ResumeTextExtractionService>();
builder.Services.AddMinioStorage(builder.Configuration);
builder.Services.AddFileService();

// ── AutoMapper ────────────────────────────────────────────────────────────────
builder.Services.AddAutoMapper(cfg =>
    cfg.AddMaps(typeof(ResumeService.Mapping.ResumeMappingProfile).Assembly));

// ── MassTransit & RabbitMQ (Publisher) ───────────────────────────────────────
builder.Services.AddMassTransit(x =>
{
    x.SetKebabCaseEndpointNameFormatter();

    x.AddConsumer<ResumeUserDeletedConsumer>();

    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.Host(
            builder.Configuration["RabbitMQ:Host"] ?? "localhost",
            ushort.Parse(builder.Configuration["RabbitMQ:Port"] ?? "5672"),
            "/",
            h =>
            {
                h.Username(builder.Configuration["RabbitMQ:Username"] ?? "guest");
                h.Password(builder.Configuration["RabbitMQ:Password"] ?? "guest");
            });

        cfg.ConfigureEndpoints(context);
    });
});

// ── Exception Handler ─────────────────────────────────────────────────────────
builder.Services.AddCommonApiServices();

// ── Controllers + Filters + FluentValidation ──────────────────────────────────
builder.Services.AddFluentValidationAutoValidation();
builder.Services.AddValidatorsFromAssemblyContaining<CreateResumeRequestValidator>();

builder.Services.AddControllers(options =>
{
    options.Filters.Add<FormatResponseFilter>();
    options.Filters.Add<PermissionInterceptor>();
})
.AddJsonOptions(options =>
{
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

app.UseCommonErrorHandling("ResumeService");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

// ── Khởi tạo & migrate DB khi startup ─────────────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db   = scope.ServiceProvider.GetRequiredService<ResumeDbContext>();
    var conn = db.Database.GetDbConnection();
    await conn.OpenAsync();

    await using var cmd = conn.CreateCommand();
    cmd.CommandText = @"
        -- ── Bảng Resumes ─────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS ""Resumes"" (
            ""Id""               uuid          NOT NULL DEFAULT gen_random_uuid(),
            ""CustomerId""       uuid          NOT NULL,
            ""Title""            varchar(300)  NOT NULL,
            ""Url""              varchar(2000),
            ""ExtractedText""    text,
            ""IsDefault""        boolean       NOT NULL DEFAULT false,
            ""IsOnlineCv""       boolean       NOT NULL DEFAULT false,
            ""TemplateId""       integer,
            ""ContentJson""      text,
            ""IsDeleted""        boolean       NOT NULL DEFAULT false,
            ""DeletedAt""        timestamptz,
            ""CreatedDate""      timestamptz   NOT NULL DEFAULT now(),
            ""LastModifiedDate"" timestamptz,
            ""CreatedBy""        varchar(255)  NOT NULL DEFAULT '',
            ""LastModifiedBy""   varchar(255),
            CONSTRAINT ""PK_Resumes"" PRIMARY KEY (""Id"")
        );

        -- ── Bảng Applications ────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS ""Applications"" (
            ""Id""               uuid          NOT NULL DEFAULT gen_random_uuid(),
            ""CustomerId""       uuid          NOT NULL,
            ""JobId""            uuid          NOT NULL,
            ""ResumeId""         uuid          NOT NULL,
            ""CoverLetter""      varchar(10000),
            ""Status""           varchar(50)   NOT NULL DEFAULT 'PENDING',
            ""ReviewNote""       varchar(5000),
            ""IsDeleted""        boolean       NOT NULL DEFAULT false,
            ""DeletedAt""        timestamptz,
            ""CreatedDate""      timestamptz   NOT NULL DEFAULT now(),
            ""LastModifiedDate"" timestamptz,
            ""CreatedBy""        varchar(255)  NOT NULL DEFAULT '',
            ""LastModifiedBy""   varchar(255),
            CONSTRAINT ""PK_Applications"" PRIMARY KEY (""Id""),
            CONSTRAINT ""FK_Applications_Resumes"" FOREIGN KEY (""ResumeId"")
                REFERENCES ""Resumes"" (""Id"") ON DELETE RESTRICT
        );

        -- ── Thêm cột CV Builder nếu chưa có (cho DB cũ đã tồn tại) ──────────
        ALTER TABLE ""Resumes"" ADD COLUMN IF NOT EXISTS ""IsOnlineCv""  boolean NOT NULL DEFAULT false;
        ALTER TABLE ""Resumes"" ADD COLUMN IF NOT EXISTS ""TemplateId""  integer;
        ALTER TABLE ""Resumes"" ADD COLUMN IF NOT EXISTS ""ContentJson"" text;
        ALTER TABLE ""Resumes"" ADD COLUMN IF NOT EXISTS ""ExtractedText"" text;

        -- ── Indexes ───────────────────────────────────────────────────────────
        CREATE INDEX IF NOT EXISTS ""IX_Resumes_CustomerId""  ON ""Resumes""      (""CustomerId"");
        CREATE INDEX IF NOT EXISTS ""IX_Resumes_IsDefault""   ON ""Resumes""      (""IsDefault"");
        CREATE INDEX IF NOT EXISTS ""IX_Resumes_IsDeleted""   ON ""Resumes""      (""IsDeleted"");
        CREATE INDEX IF NOT EXISTS ""IX_Resumes_IsOnlineCv""  ON ""Resumes""      (""IsOnlineCv"");
        CREATE INDEX IF NOT EXISTS ""IX_Applications_CustomerId"" ON ""Applications"" (""CustomerId"");
        CREATE INDEX IF NOT EXISTS ""IX_Applications_JobId""     ON ""Applications"" (""JobId"");
        CREATE INDEX IF NOT EXISTS ""IX_Applications_ResumeId""  ON ""Applications"" (""ResumeId"");
        CREATE INDEX IF NOT EXISTS ""IX_Applications_Status""    ON ""Applications"" (""Status"");
        CREATE INDEX IF NOT EXISTS ""IX_Applications_IsDeleted"" ON ""Applications"" (""IsDeleted"");
        CREATE UNIQUE INDEX IF NOT EXISTS ""IX_Applications_Customer_Job_Unique""
            ON ""Applications"" (""CustomerId"", ""JobId"") WHERE ""IsDeleted"" = false;
    ";
    await cmd.ExecuteNonQueryAsync();
    await conn.CloseAsync();
}

// ── Quét và trích xuất text cho các CV cũ chưa có ExtractedText (chạy ngầm) ──
_ = Task.Run(async () =>
{
    try
    {
        await Task.Delay(5000); // Chờ container MinIO/DB sẵn sàng
        using var scope = app.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<ResumeDbContext>();
        var extractor = scope.ServiceProvider.GetRequiredService<IResumeTextExtractionService>();
        var fileService = scope.ServiceProvider.GetRequiredService<CommonService.File.IFileService>();
        
        var legacyResumes = db.Resumes
            .Where(r => !r.IsDeleted && !r.IsOnlineCv && r.Url != null && (r.ExtractedText == null || r.ExtractedText == ""))
            .ToList();
            
        if (legacyResumes.Any())
        {
            Console.WriteLine($"[Startup] Phát hiện {legacyResumes.Count} CV cũ chưa trích xuất text. Đang chạy trích xuất ngầm...");
            foreach (var resume in legacyResumes)
            {
                try
                {
                    using var stream = await fileService.DownloadAsync("resumes", resume.Url);
                    var text = await extractor.ExtractAsync(stream, resume.Url);
                    if (!string.IsNullOrEmpty(text))
                    {
                        resume.ExtractedText = text;
                        db.Resumes.Update(resume);
                        Console.WriteLine($"[Startup] Đã tự động cập nhật text cho CV cũ: {resume.Title} (ID: {resume.Id})");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[Startup] Lỗi trích xuất CV cũ {resume.Title} (ID: {resume.Id}): {ex.Message}");
                }
            }
            await db.SaveChangesAsync();
            Console.WriteLine("[Startup] Đã hoàn tất xử lý các CV cũ ngầm.");
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Startup] Lỗi trong quá trình quét CV cũ: {ex.Message}");
    }
});

app.Run();


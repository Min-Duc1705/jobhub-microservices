using System.Text;
using CommonService.Extensions;
using CommonService.Filters;
using FluentValidation;
using FluentValidation.AspNetCore;
using JobService.Data;
using JobService.Repositories;
using JobService.Repositories.Interface;
using JobService.Services;
using JobService.Services.Interface;
using JobService.Validators;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using MassTransit;
using JobService.Consumers;

var builder = WebApplication.CreateBuilder(args);

// ── Database (PostgreSQL) ──────────────────────────────────────────────────────
builder.Services.AddDbContext<JobDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("JobDb")));

// ── Redis Cache (đọc permissions từ Auth namespace) ────────────────────────────
builder.Services.AddCommonRedisCache(builder.Configuration, "JobHubAuth_");

// ── Repositories ──────────────────────────────────────────────────────────────
builder.Services.AddScoped<IJobRepository,      JobRepository>();
builder.Services.AddScoped<ISkillRepository,    SkillRepository>();
builder.Services.AddScoped<ISavedJobRepository, SavedJobRepository>();

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<IJobService,      JobServiceImpl>();
builder.Services.AddScoped<ISkillService,    SkillServiceImpl>();
builder.Services.AddScoped<ISavedJobService, SavedJobServiceImpl>();
builder.Services.AddMinioStorage(builder.Configuration);


// ── AutoMapper ────────────────────────────────────────────────────────────────
builder.Services.AddAutoMapper(cfg =>
    cfg.AddMaps(typeof(JobService.Mapping.JobMappingProfile).Assembly));

// ── MassTransit & RabbitMQ (Publisher) ───────────────────────────────────────
builder.Services.AddMassTransit(x =>
{
    x.SetKebabCaseEndpointNameFormatter();

    x.AddConsumer<ApplicationSubmittedConsumer>();
    x.AddConsumer<ApplicationStatusChangedConsumer>();
    x.AddConsumer<JobUserDeletedConsumer>();

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
builder.Services.AddValidatorsFromAssemblyContaining<CreateJobRequestValidator>();

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

app.UseCommonErrorHandling("JobService");

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
    var db = scope.ServiceProvider.GetRequiredService<JobDbContext>();
    await db.Database.MigrateAsync();
}

app.Run();

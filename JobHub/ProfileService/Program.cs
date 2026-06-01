using System.Text;
using CommonService.Exceptions;
using CommonService.Extensions;
using CommonService.Filters;
using FluentValidation;
using FluentValidation.AspNetCore;
using MassTransit;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using ProfileService.Consumers;
using ProfileService.Data;
using ProfileService.Repositories;
using ProfileService.Repositories.Interface;
using ProfileService.Services;
using ProfileService.Services.Interface;
using ProfileService.Validators;

var builder = WebApplication.CreateBuilder(args);

// ── Database (PostgreSQL) ──────────────────────────────────────────────────────
builder.Services.AddDbContext<ProfileDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("ProfileDb")));

// ── Redis Cache ────────────────────────────────────────────────────────────────
builder.Services.AddCommonRedisCache(builder.Configuration, "JobHubAuth_");

// ── Repositories ──────────────────────────────────────────────────────────────
builder.Services.AddScoped<ICustomerRepository, CustomerRepository>();
builder.Services.AddScoped<ISkillRepository, SkillRepository>();

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<ICustomerService, CustomerServiceImpl>();
builder.Services.AddScoped<ISkillService, SkillServiceImpl>();
builder.Services.AddMinioStorage(builder.Configuration);
builder.Services.AddFileService();

// ── AutoMapper ────────────────────────────────────────────────────────────────
builder.Services.AddAutoMapper(cfg => cfg.AddMaps(typeof(ProfileService.Mapping.ProfileMappingProfile).Assembly));

// ── MassTransit & RabbitMQ (Consumers) ────────────────────────────────────────
builder.Services.AddMassTransit(x =>
{
    x.SetKebabCaseEndpointNameFormatter();

    x.AddConsumer<UserRegisteredEventConsumer>();
    x.AddConsumer<SkillCreatedConsumer>();
    x.AddConsumer<SkillUpdatedConsumer>();
    x.AddConsumer<SkillDeletedConsumer>();

    // Outbox cho ProfileService
    x.AddEntityFrameworkOutbox<ProfileDbContext>(o =>
    {
        o.UsePostgres();
        o.UseBusOutbox();
    });

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

// ── Exception Handler ────────────────────────────────────────────────────────
builder.Services.AddCommonApiServices();

// ── Controllers + Filters ──────────────────────────────────────────────────────────────
// FluentValidation v11: tách biệt khỏi AddControllers
builder.Services.AddFluentValidationAutoValidation();
builder.Services.AddValidatorsFromAssemblyContaining<UpdateCustomerRequestValidator>();

builder.Services.AddControllers(options =>
{
    options.Filters.Add<FormatResponseFilter>();
    options.Filters.Add<PermissionInterceptor>();
})
.AddJsonOptions(opts =>
{
    // Cho phép deserialize enum từ string ("MALE", "FEMALE", "ACTIVELY_LOOKING"...)
    opts.JsonSerializerOptions.Converters.Add(
        new System.Text.Json.Serialization.JsonStringEnumConverter());
});

// ── JWT Authentication ────────────────────────────────────────────────────────
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

var app = builder.Build();

app.UseCommonErrorHandling("ProfileService");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

// ── Database Migration ────────────────────────────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ProfileDbContext>();
    await db.Database.MigrateAsync(); // Tạo schema (bảng) tự động khi khởi động
}

app.Run();


using System.Text;
using AuthService.Data;
using AuthService.Repositories;
using AuthService.Repositories.Interface;
using AuthService.SeedData;
using AuthService.Services;
using AuthService.Services.Interface;
using AuthService.Validators;
using CommonService.Extensions;
using CommonService.Filters;
using FluentValidation;
using FluentValidation.AspNetCore;
using MassTransit;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using CommonService.Common;
using CommonService.Exceptions;

var builder = WebApplication.CreateBuilder(args);

// ── Database (PostgreSQL) ──────────────────────────────────────────────────────
builder.Services.AddDbContext<AuthDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("AuthDb")));

// ── Redis Cache ────────────────────────────────────────────────────────────────
builder.Services.AddCommonRedisCache(builder.Configuration, "JobHubAuth_");


// ── Repositories ──────────────────────────────────────────────────────────────
builder.Services.AddScoped<IAppUserRepository, AppUserRepository>();
builder.Services.AddScoped<IRoleRepository,    RoleRepository>();
builder.Services.AddScoped<IPermissionRepository, PermissionRepository>();

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddHttpContextAccessor();
builder.Services.AddHttpClient();
builder.Services.AddScoped<ITokenService,      TokenServiceImpl>();
builder.Services.AddScoped<IAuthService,       AuthServiceImpl>();
builder.Services.AddScoped<IRoleService,       RoleServiceImpl>();
builder.Services.AddScoped<IUserService,       UserServiceImpl>();
builder.Services.AddScoped<IPermissionService, PermissionServiceImpl>();


// ── AutoMapper ────────────────────────────────────────────────────────────────
builder.Services.AddAutoMapper(cfg => cfg.AddMaps(typeof(AuthService.Mapping.AuthMappingProfile).Assembly));

// ── MassTransit & RabbitMQ (Transactional Outbox Pattern) ────────────────────
builder.Services.AddMassTransit(x =>
{
    x.SetKebabCaseEndpointNameFormatter();

    // Outbox Pattern: Event lưu vào bảng OutboxMessages cùng Transaction với DB
    // → Không bao giờ mất Event kể cả khi RabbitMQ down
    x.AddEntityFrameworkOutbox<AuthDbContext>(o =>
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
builder.Services.AddValidatorsFromAssemblyContaining<RegisterRequestValidator>();

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

        // ── Trả ApiResponse JSON chuẩn khi JWT 401/403 ──────────────────────
        options.Events = new JwtBearerEvents
        {
            OnChallenge = async context =>
            {
                context.HandleResponse();
                context.Response.StatusCode  = 401;
                context.Response.ContentType = "application/json";

                var message  = string.IsNullOrEmpty(context.ErrorDescription)
                    ? "Bạn chưa đăng nhập hoặc token đã hết hạn."
                    : context.ErrorDescription;

                var response = new ApiResponse<object>
                {
                    StatusCode = 401,
                    Error      = "Unauthorized",
                    Message    = message,
                    Data       = null
                };

                await context.Response.WriteAsJsonAsync(response);
            },

            OnForbidden = async context =>
            {
                context.Response.StatusCode  = 403;
                context.Response.ContentType = "application/json";

                var response = new ApiResponse<object>
                {
                    StatusCode = 403,
                    Error      = "Forbidden",
                    Message    = "Bạn không có quyền truy cập tài nguyên này.",
                    Data       = null
                };

                await context.Response.WriteAsJsonAsync(response);
            }
        };
    });
builder.Services.AddAuthorization();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// ── Pipeline ──────────────────────────────────────────────────────────────────
var app = builder.Build();

app.UseCommonErrorHandling("AuthService");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

// ── Database Migration + Seeder ──────────────────────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db           = scope.ServiceProvider.GetRequiredService<AuthDbContext>();
    var cacheService = scope.ServiceProvider.GetRequiredService<CommonService.Caching.ICacheService>();
    await db.Database.MigrateAsync();
    await DatabaseSeeder.SeedAsync(db, cacheService);
}


app.Run();

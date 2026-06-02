using CommonService.Extensions;
using CommonService.Filters;
using MassTransit;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Builder;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.IdentityModel.Tokens;
using NotificationService.Consumers;
using NotificationService.Data;
using NotificationService.Hubs;
using NotificationService.Services;
using NotificationService.Services.Interface;
using NotificationService.Repositories;
using NotificationService.Repositories.Interface;
using System;
using System.Text;
using System.Threading.Tasks;

var builder = WebApplication.CreateBuilder(args);

// ── Database (PostgreSQL) ──────────────────────────────────────────────────────
builder.Services.AddDbContext<NotificationDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("NotificationDb")));

// ── Redis Cache (đọc permissions từ Auth namespace) ────────────────────────────
builder.Services.AddCommonRedisCache(builder.Configuration, "JobHubAuth_");

// ── Repositories ──────────────────────────────────────────────────────────────
builder.Services.AddScoped<INotificationRepository, NotificationRepository>();
builder.Services.AddScoped<IAuditLogRepository, AuditLogRepository>();
builder.Services.AddScoped<IChatRepository, ChatRepository>();

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<IEmailService, EmailService>();
builder.Services.AddScoped<INotificationService, NotificationServiceImpl>();
builder.Services.AddScoped<IAuditLogService, AuditLogServiceImpl>();
builder.Services.AddScoped<IChatService, ChatServiceImpl>();

// ── AutoMapper ────────────────────────────────────────────────────────────────
builder.Services.AddAutoMapper(cfg => cfg.AddMaps(typeof(NotificationService.Mapping.NotificationMappingProfile).Assembly));

// ── CORS ───────────────────────────────────────────────────────────────────────
builder.Services.AddCors(options =>
{
    options.AddPolicy("SignalrCorsPolicy", policy =>
    {
        policy.SetIsOriginAllowed(origin => true) // Cho phép tất cả các nguồn (gồm Ngrok, Vercel, Localhost)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

// ── SignalR ───────────────────────────────────────────────────────────────────
builder.Services.AddSignalR();

// ── MassTransit & RabbitMQ (Consumers) ────────────────────────────────────────
builder.Services.AddMassTransit(x =>
{
    x.SetKebabCaseEndpointNameFormatter();

    // Register Consumers
    x.AddConsumer<OtpRequestedConsumer>();
    x.AddConsumer<SendNotificationConsumer>();
    x.AddConsumer<AuditLogCreatedConsumer>();

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

// ── Exception Handler & Common API Services ───────────────────────────────────
builder.Services.AddCommonApiServices();

// ── Controllers + Filters ──────────────────────────────────────────────────────
builder.Services.AddControllers(options =>
{
    options.Filters.Add<FormatResponseFilter>();
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

        // Extract token from query string for SignalR WebSocket connections
        options.Events = new JwtBearerEvents
        {
            OnMessageReceived = context =>
            {
                var accessToken = context.Request.Query["access_token"];

                var path = context.HttpContext.Request.Path;
                if (!string.IsNullOrEmpty(accessToken) &&
                    (path.StartsWithSegments("/ws/notifications") || path.StartsWithSegments("/ws/chat")))
                {
                    context.Token = accessToken;
                }
                return Task.CompletedTask;
            }
        };
    });

builder.Services.AddAuthorization();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

app.UseCommonErrorHandling("NotificationService");

app.UseCors("SignalrCorsPolicy");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
app.MapHub<NotificationHub>("/ws/notifications");
app.MapHub<ChatHub>("/ws/chat");

// ── Database Migration ────────────────────────────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<NotificationDbContext>();
    await db.Database.EnsureCreatedAsync();

    // Đảm bảo bảng AuditLogs được tạo nếu DB đã tồn tại trước đó
    var conn = db.Database.GetDbConnection();
    await conn.OpenAsync();
    await using var cmd = conn.CreateCommand();
    cmd.CommandText = @"
        CREATE TABLE IF NOT EXISTS ""AuditLogs"" (
            ""Id""          uuid          NOT NULL,
            ""UserId""      text,
            ""Email""       text,
            ""Username""    text,
            ""Action""      text          NOT NULL,
            ""EntityName""  text          NOT NULL,
            ""EntityId""    text          NOT NULL,
            ""ChangesJson"" text,
            ""IpAddress""   text,
            ""UserAgent""   text,
            ""Timestamp""   timestamptz   NOT NULL,
            ""IsDeleted""   boolean       NOT NULL DEFAULT FALSE,
            ""DeletedAt""   timestamptz,
            CONSTRAINT ""PK_AuditLogs"" PRIMARY KEY (""Id"")
        );
        ALTER TABLE ""AuditLogs"" ADD COLUMN IF NOT EXISTS ""Username"" text;
        ALTER TABLE ""AuditLogs"" ADD COLUMN IF NOT EXISTS ""IsDeleted"" boolean NOT NULL DEFAULT FALSE;
        ALTER TABLE ""AuditLogs"" ADD COLUMN IF NOT EXISTS ""DeletedAt"" timestamptz;
        CREATE INDEX IF NOT EXISTS ""IX_AuditLogs_Email"" ON ""AuditLogs"" (""Email"");
        CREATE INDEX IF NOT EXISTS ""IX_AuditLogs_Username"" ON ""AuditLogs"" (""Username"");
        CREATE INDEX IF NOT EXISTS ""IX_AuditLogs_Action"" ON ""AuditLogs"" (""Action"");
        CREATE INDEX IF NOT EXISTS ""IX_AuditLogs_EntityName"" ON ""AuditLogs"" (""EntityName"");
        CREATE INDEX IF NOT EXISTS ""IX_AuditLogs_Timestamp"" ON ""AuditLogs"" (""Timestamp"" DESC);
        CREATE INDEX IF NOT EXISTS ""IX_AuditLogs_IsDeleted"" ON ""AuditLogs"" (""IsDeleted"");

        CREATE TABLE IF NOT EXISTS ""Conversations"" (
            ""Id""                   uuid          NOT NULL,
            ""ParticipantA""         text          NOT NULL,
            ""ParticipantB""         text          NOT NULL,
            ""LastMessageContent""   text,
            ""LastMessageAt""        timestamptz,
            ""CreatedAt""            timestamptz   NOT NULL,
            ""IsDeleted""            boolean       NOT NULL DEFAULT FALSE,
            ""DeletedAt""            timestamptz,
            CONSTRAINT ""PK_Conversations"" PRIMARY KEY (""Id"")
        );
        CREATE INDEX IF NOT EXISTS ""IX_Conversations_ParticipantA"" ON ""Conversations"" (""ParticipantA"");
        CREATE INDEX IF NOT EXISTS ""IX_Conversations_ParticipantB"" ON ""Conversations"" (""ParticipantB"");
        CREATE INDEX IF NOT EXISTS ""IX_Conversations_IsDeleted"" ON ""Conversations"" (""IsDeleted"");

        CREATE TABLE IF NOT EXISTS ""Messages"" (
            ""Id""             uuid          NOT NULL,
            ""ConversationId"" uuid          NOT NULL,
            ""SenderId""       text          NOT NULL,
            ""Content""        text          NOT NULL,
            ""Type""           text          NOT NULL DEFAULT 'text',
            ""IsRead""         boolean       NOT NULL DEFAULT FALSE,
            ""CreatedAt""      timestamptz   NOT NULL,
            ""IsDeleted""      boolean       NOT NULL DEFAULT FALSE,
            ""DeletedAt""      timestamptz,
            CONSTRAINT ""PK_Messages"" PRIMARY KEY (""Id""),
            CONSTRAINT ""FK_Messages_Conversations_ConversationId"" FOREIGN KEY (""ConversationId"") REFERENCES ""Conversations"" (""Id"") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS ""IX_Messages_ConversationId"" ON ""Messages"" (""ConversationId"");
        CREATE INDEX IF NOT EXISTS ""IX_Messages_SenderId"" ON ""Messages"" (""SenderId"");
        CREATE INDEX IF NOT EXISTS ""IX_Messages_CreatedAt"" ON ""Messages"" (""CreatedAt"" DESC);
        CREATE INDEX IF NOT EXISTS ""IX_Messages_IsDeleted"" ON ""Messages"" (""IsDeleted"");
    ";
    await cmd.ExecuteNonQueryAsync();
    await conn.CloseAsync();
}

app.Run();

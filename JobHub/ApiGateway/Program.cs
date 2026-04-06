using ApiGateway.Config;
using Ocelot.DependencyInjection;
using Ocelot.Middleware;

var builder = WebApplication.CreateBuilder(args);

// ── Load ocelot.json ───────────────────────────────────────────────────────────
builder.Configuration.AddJsonFile("ocelot.json", optional: false, reloadOnChange: true);

// ── CORS ───────────────────────────────────────────────────────────────────────
builder.Services.AddAppCors();

// ── JWT Authentication (validate Access Token) ─────────────────────────────────
builder.Services.AddAppJwt(builder.Configuration);

// ── Ocelot ─────────────────────────────────────────────────────────────────────
builder.Services.AddOcelot();

// ── Build ──────────────────────────────────────────────────────────────────────
var app = builder.Build();

// ── Middleware pipeline ────────────────────────────────────────────────────────

// Wrap 401/403/404/500 từ Ocelot thành ApiResponse JSON chuẩn
app.UseMiddleware<OcelotErrorResponseMiddleware>();

app.UseCors(CorsConfiguration.PolicyName);

app.UseAuthentication();
app.UseAuthorization();

// Ocelot phải là middleware cuối cùng
await app.UseOcelot();

app.Run();

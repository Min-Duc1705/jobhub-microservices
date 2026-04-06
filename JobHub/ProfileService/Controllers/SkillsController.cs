using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ProfileService.Models.Request;
using ProfileService.Models.Response;
using ProfileService.Services.Interface;
using System.Security.Claims;

namespace ProfileService.Controllers;

[ApiController]
[Route("api/v1/skills")]
[Authorize]
public class SkillsController : ControllerBase
{
    private readonly ISkillService _skillService;

    public SkillsController(ISkillService skillService)
    {
        _skillService = skillService;
    }

    private Guid GetCurrentUserId()
    {
        var sub = User.FindFirstValue(ClaimTypes.NameIdentifier)
               ?? User.FindFirstValue("sub")
               ?? throw new UnauthorizedAccessException("Không tìm thấy thông tin User trong token.");
        return Guid.Parse(sub);
    }

    // GET /api/v1/skills?searchTerm=react&pageNumber=1&pageSize=10  — Admin quản trị
    [HttpGet]
    [ApiMessage("Lấy danh sách kỹ năng thành công")]
    [RequiresPermission("GET", "/api/v1/skills")]
    public async Task<ActionResult<ResultPaginationDto<SkillResponse>>> GetAll([FromQuery] SkillFilterRequest filter)
    {
        return Ok(await _skillService.GetAllAsync(filter));
    }

    // GET /api/v1/skills/dropdown — Mọi user đã login có thể dùng để chọn skill
    [HttpGet("dropdown")]
    [ApiMessage("Lấy danh sách kỹ năng (dropdown) thành công")]
    public async Task<ActionResult<List<SkillResponse>>> GetDropdown()
    {
        return Ok(await _skillService.GetDropdownAsync());
    }

    // GET /api/v1/skills/{id}
    [HttpGet("{id:guid}")]
    [ApiMessage("Lấy thông tin kỹ năng thành công")]
    public async Task<ActionResult<SkillResponse>> GetById(Guid id)
    {
        return Ok(await _skillService.GetByIdAsync(id));
    }

    // POST /api/v1/skills — Chỉ Admin mới được tạo Skill mới
    [HttpPost]
    [ApiMessage("Tạo kỹ năng mới thành công")]
    [RequiresPermission("POST", "/api/v1/skills")]
    public async Task<ActionResult<SkillResponse>> Create([FromBody] CreateSkillRequest request)
    {
        var skill = await _skillService.CreateAsync(request);
        return StatusCode(201, skill);
    }

    // PUT /api/v1/skills/{id} — Chỉ Admin
    [HttpPut("{id:guid}")]
    [ApiMessage("Cập nhật kỹ năng thành công")]
    [RequiresPermission("PUT", "/api/v1/skills/{id}")]
    public async Task<ActionResult<SkillResponse>> Update(Guid id, [FromBody] UpdateSkillRequest request)
    {
        return Ok(await _skillService.UpdateAsync(id, request));
    }

    // DELETE /api/v1/skills/{id} — Chỉ Admin
    [HttpDelete("{id:guid}")]
    [ApiMessage("Xóa kỹ năng thành công")]
    [RequiresPermission("DELETE", "/api/v1/skills/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _skillService.DeleteAsync(id);
        return Ok(null);
    }

    // ── Quản lý kỹ năng cá nhân ─────────────────────────────────────────────

    // POST /api/v1/skills/me — User tự thêm kỹ năng vào hồ sơ
    [HttpPost("me")]
    [ApiMessage("Thêm kỹ năng vào hồ sơ thành công")]
    public async Task<ActionResult<CustomerResponse>> AddToMyProfile([FromBody] AddCustomerSkillRequest request)
    {
        return Ok(await _skillService.AddSkillToCustomerAsync(GetCurrentUserId(), request));
    }

    // DELETE /api/v1/skills/me/{skillId} — User tự xoá kỹ năng khỏi hồ sơ
    [HttpDelete("me/{skillId:guid}")]
    [ApiMessage("Xóa kỹ năng khỏi hồ sơ thành công")]
    public async Task<ActionResult<CustomerResponse>> RemoveFromMyProfile(Guid skillId)
    {
        return Ok(await _skillService.RemoveSkillFromCustomerAsync(GetCurrentUserId(), skillId));
    }
}

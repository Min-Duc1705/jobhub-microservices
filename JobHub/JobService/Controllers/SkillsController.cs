using CommonService.Annotations;
using CommonService.Common;
using CommonService.Filters;
using JobService.Models.Request;
using JobService.Models.Response;
using JobService.Services.Interface;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace JobService.Controllers;

[ApiController]
[Route("api/v1/skills")]
public class SkillsController : ControllerBase
{
    private readonly ISkillService _skillService;

    public SkillsController(ISkillService skillService) => _skillService = skillService;

    // GET /api/v1/skills (public)
    [HttpGet]
    [AllowAnonymous]
    [ApiMessage("Lấy danh sách kỹ năng thành công")]
    public async Task<ActionResult<ResultPaginationDto<SkillResponse>>> GetAll(
        [FromQuery] string? searchTerm,
        [FromQuery] string? sortBy = "name",
        [FromQuery] bool isDescending = false,
        [FromQuery] int pageNumber = 1,
        [FromQuery] int pageSize = 50)
        => Ok(await _skillService.GetAllAsync(searchTerm, sortBy, isDescending, pageNumber, pageSize));

    // GET /api/v1/skills/dropdown (public)
    [HttpGet("dropdown")]
    [AllowAnonymous]
    [ApiMessage("Lấy danh sách kỹ năng (dropdown) thành công")]
    public async Task<ActionResult<List<SkillResponse>>> GetDropdown()
    {
        var result = await _skillService.GetAllAsync(null, "name", false, 1, 1000);
        return Ok(result.Result);
    }

    // GET /api/v1/skills/{id} (public)
    [HttpGet("{id:guid}")]
    [AllowAnonymous]
    [ApiMessage("Lấy thông tin kỹ năng thành công")]
    public async Task<ActionResult<SkillResponse>> GetById(Guid id)
        => Ok(await _skillService.GetByIdAsync(id));

    // POST /api/v1/skills (Admin)
    [HttpPost]
    [Authorize]
    [ApiMessage("Tạo kỹ năng thành công")]
    [RequiresPermission("POST", "/api/v1/skills")]
    public async Task<ActionResult<SkillResponse>> Create([FromBody] CreateSkillRequest request)
    {
        var result = await _skillService.CreateAsync(request);
        return StatusCode(201, result);
    }

    // PUT /api/v1/skills/{id} (Admin)
    [HttpPut("{id:guid}")]
    [Authorize]
    [ApiMessage("Cập nhật kỹ năng thành công")]
    [RequiresPermission("PUT", "/api/v1/skills/{id}")]
    public async Task<ActionResult<SkillResponse>> Update(Guid id, [FromBody] UpdateSkillRequest request)
        => Ok(await _skillService.UpdateAsync(id, request));

    // DELETE /api/v1/skills/{id} (Admin)
    [HttpDelete("{id:guid}")]
    [Authorize]
    [ApiMessage("Xóa kỹ năng thành công")]
    [RequiresPermission("DELETE", "/api/v1/skills/{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        await _skillService.DeleteAsync(id);
        return Ok((object?)null);
    }
}

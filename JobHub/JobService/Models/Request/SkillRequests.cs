namespace JobService.Models.Request;

/// <summary>Tạo kỹ năng mới (Admin).</summary>
public class CreateSkillRequest
{
    public string Name { get; set; } = string.Empty;
}

/// <summary>Cập nhật kỹ năng.</summary>
public class UpdateSkillRequest
{
    public string Name { get; set; } = string.Empty;
}

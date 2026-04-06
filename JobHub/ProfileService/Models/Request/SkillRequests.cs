namespace ProfileService.Models.Request;

public class CreateSkillRequest
{
    public string Name { get; set; } = string.Empty;
}

public class UpdateSkillRequest
{
    public string Name { get; set; } = string.Empty;
}

public class AddCustomerSkillRequest
{
    public Guid SkillId            { get; set; }
    public int? YearsOfExperience  { get; set; }
}

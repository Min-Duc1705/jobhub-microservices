using System;
using System.Collections.Generic;

namespace CommonService.Events;

public class JobPublishedEvent
{
    public Guid JobId { get; set; }
    public string JobTitle { get; set; } = string.Empty;
    public int YearsOfExperience { get; set; }
    public List<string> SkillSet { get; set; } = new();
    public string Location { get; set; } = string.Empty;
    public string Level { get; set; } = string.Empty;
    public double SalaryMin { get; set; }
    public double SalaryMax { get; set; }
    public bool IsNegotiable { get; set; }
}

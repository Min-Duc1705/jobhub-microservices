using FluentValidation;
using JobService.Models.Request;

namespace JobService.Validators;

public class CreateJobRequestValidator : AbstractValidator<CreateJobRequest>
{
    public CreateJobRequestValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tên vị trí tuyển dụng không được để trống.")
            .MaximumLength(300).WithMessage("Tên không được vượt quá 300 ký tự.");

        RuleFor(x => x.CompanyId)
            .NotEmpty().WithMessage("CompanyId không được để trống.");

        RuleFor(x => x.Quantity)
            .GreaterThan(0).WithMessage("Số lượng tuyển phải lớn hơn 0.");

        RuleFor(x => x.SalaryMin)
            .GreaterThanOrEqualTo(0).WithMessage("Mức lương tối thiểu không được âm.")
            .When(x => x.SalaryMin.HasValue);

        RuleFor(x => x.SalaryMax)
            .GreaterThanOrEqualTo(0).WithMessage("Mức lương tối đa không được âm.")
            .GreaterThanOrEqualTo(x => x.SalaryMin ?? 0)
            .WithMessage("Mức lương tối đa phải lớn hơn hoặc bằng mức tối thiểu.")
            .When(x => x.SalaryMax.HasValue);

        RuleFor(x => x.EndDate)
            .GreaterThan(DateTime.UtcNow).WithMessage("Ngày kết thúc phải là ngày trong tương lai.")
            .When(x => x.EndDate.HasValue);

        RuleFor(x => x.Description)
            .MaximumLength(20000).WithMessage("Mô tả không được vượt quá 20000 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Description));
    }
}

public class UpdateJobRequestValidator : AbstractValidator<UpdateJobRequest>
{
    public UpdateJobRequestValidator()
    {
        RuleFor(x => x.Name)
            .MaximumLength(300).WithMessage("Tên không được vượt quá 300 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Name));

        RuleFor(x => x.Quantity)
            .GreaterThan(0).WithMessage("Số lượng tuyển phải lớn hơn 0.")
            .When(x => x.Quantity.HasValue);

        RuleFor(x => x.SalaryMin)
            .GreaterThanOrEqualTo(0).WithMessage("Mức lương tối thiểu không được âm.")
            .When(x => x.SalaryMin.HasValue);

        RuleFor(x => x.SalaryMax)
            .GreaterThanOrEqualTo(0).WithMessage("Mức lương tối đa không được âm.")
            .GreaterThanOrEqualTo(x => x.SalaryMin ?? 0)
            .WithMessage("Mức lương tối đa phải lớn hơn hoặc bằng mức tối thiểu.")
            .When(x => x.SalaryMax.HasValue);

        RuleFor(x => x.EndDate)
            .GreaterThan(DateTime.UtcNow).WithMessage("Ngày kết thúc phải là ngày trong tương lai.")
            .When(x => x.EndDate.HasValue);
    }
}

public class CreateSkillRequestValidator : AbstractValidator<CreateSkillRequest>
{
    public CreateSkillRequestValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tên kỹ năng không được để trống.")
            .MinimumLength(2).WithMessage("Tên kỹ năng phải có ít nhất 2 ký tự.")
            .MaximumLength(100).WithMessage("Tên kỹ năng không được vượt quá 100 ký tự.");
    }
}

public class UpdateSkillRequestValidator : AbstractValidator<UpdateSkillRequest>
{
    public UpdateSkillRequestValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tên kỹ năng không được để trống.")
            .MinimumLength(2).WithMessage("Tên kỹ năng phải có ít nhất 2 ký tự.")
            .MaximumLength(100).WithMessage("Tên kỹ năng không được vượt quá 100 ký tự.");
    }
}

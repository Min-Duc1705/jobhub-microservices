using FluentValidation;
using ProfileService.Models.Request;

namespace ProfileService.Validators;

public class UpdateCustomerRequestValidator : AbstractValidator<UpdateCustomerRequest>
{
    public UpdateCustomerRequestValidator()
    {
        RuleFor(x => x.Phone)
            .Matches(@"^[0-9]{10,11}$").WithMessage("Số điện thoại phải có 10-11 chữ số.")
            .When(x => !string.IsNullOrEmpty(x.Phone));

        RuleFor(x => x.DateOfBirth)
            .LessThan(DateTime.UtcNow.AddYears(-16)).WithMessage("Bạn phải ít nhất 16 tuổi.")
            .When(x => x.DateOfBirth.HasValue);

        RuleFor(x => x.YearsOfExperience)
            .InclusiveBetween(0, 50).WithMessage("Số năm kinh nghiệm phải từ 0 đến 50.")
            .When(x => x.YearsOfExperience.HasValue);

        RuleFor(x => x.ExpectedSalary)
            .GreaterThanOrEqualTo(0).WithMessage("Mức lương kỳ vọng không được âm.")
            .When(x => x.ExpectedSalary.HasValue);

        RuleFor(x => x.FullName)
            .MaximumLength(100).WithMessage("Họ tên không được vượt quá 100 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.FullName));

        RuleFor(x => x.Summary)
            .MaximumLength(2000).WithMessage("Giới thiệu bản thân không được vượt quá 2000 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Summary));
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

public class AddCustomerSkillRequestValidator : AbstractValidator<AddCustomerSkillRequest>
{
    public AddCustomerSkillRequestValidator()
    {
        RuleFor(x => x.SkillId)
            .NotEmpty().WithMessage("SkillId không được để trống.");

        RuleFor(x => x.YearsOfExperience)
            .InclusiveBetween(0, 50).WithMessage("Số năm kinh nghiệm phải từ 0 đến 50.")
            .When(x => x.YearsOfExperience.HasValue);
    }
}

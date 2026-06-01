using FluentValidation;
using ResumeService.Models.Request;

namespace ResumeService.Validators;

public class CreateApplicationRequestValidator : AbstractValidator<CreateApplicationRequest>
{
    public CreateApplicationRequestValidator()
    {
        RuleFor(x => x.JobId)
            .NotEmpty().WithMessage("JobId không được để trống.");

        RuleFor(x => x.ResumeId)
            .NotEmpty().WithMessage("ResumeId không được để trống.");

        RuleFor(x => x.CoverLetter)
            .MaximumLength(10000).WithMessage("Thư xin việc không được vượt quá 10000 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.CoverLetter));
    }
}

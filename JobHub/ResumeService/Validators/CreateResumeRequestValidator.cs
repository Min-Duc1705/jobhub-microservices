using FluentValidation;
using ResumeService.Models.Request;

namespace ResumeService.Validators;

public class CreateResumeRequestValidator : AbstractValidator<CreateResumeRequest>
{
    public CreateResumeRequestValidator()
    {
        RuleFor(x => x.Title)
            .NotEmpty().WithMessage("Tiêu đề CV không được để trống.")
            .MaximumLength(300).WithMessage("Tiêu đề không được vượt quá 300 ký tự.");

        RuleFor(x => x.Url)
            .NotEmpty().WithMessage("URL file CV không được để trống.")
            .MaximumLength(2000).WithMessage("URL không được vượt quá 2000 ký tự.");
    }
}

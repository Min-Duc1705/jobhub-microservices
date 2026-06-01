using FluentValidation;
using ResumeService.Models.Request;

namespace ResumeService.Validators;

public class UpdateResumeRequestValidator : AbstractValidator<UpdateResumeRequest>
{
    public UpdateResumeRequestValidator()
    {
        RuleFor(x => x.Title)
            .MaximumLength(300).WithMessage("Tiêu đề không được vượt quá 300 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Title));

        RuleFor(x => x.Url)
            .MaximumLength(2000).WithMessage("URL không được vượt quá 2000 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Url));
    }
}

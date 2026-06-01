using FluentValidation;
using ResumeService.Models.Request;

namespace ResumeService.Validators;

public class UpdateApplicationStatusRequestValidator : AbstractValidator<UpdateApplicationStatusRequest>
{
    public UpdateApplicationStatusRequestValidator()
    {
        RuleFor(x => x.Status)
            .IsInEnum().WithMessage("Trạng thái không hợp lệ.");

        RuleFor(x => x.ReviewNote)
            .MaximumLength(5000).WithMessage("Ghi chú không được vượt quá 5000 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.ReviewNote));
    }
}

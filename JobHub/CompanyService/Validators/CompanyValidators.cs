using FluentValidation;
using CompanyService.Models.Request;

namespace CompanyService.Validators;

public class CreateCompanyRequestValidator : AbstractValidator<CreateCompanyRequest>
{
    public CreateCompanyRequestValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tên công ty không được để trống.")
            .MinimumLength(2).WithMessage("Tên công ty phải có ít nhất 2 ký tự.")
            .MaximumLength(200).WithMessage("Tên công ty không được vượt quá 200 ký tự.");

        RuleFor(x => x.ContactEmail)
            .EmailAddress().WithMessage("Email liên hệ không hợp lệ.")
            .When(x => !string.IsNullOrEmpty(x.ContactEmail));

        RuleFor(x => x.Website)
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _))
            .WithMessage("Website phải là URL hợp lệ (bắt đầu bằng http:// hoặc https://).")
            .When(x => !string.IsNullOrEmpty(x.Website));

        RuleFor(x => x.TaxCode)
            .Matches(@"^\d{10,13}$").WithMessage("Mã số thuế phải có 10-13 chữ số.")
            .When(x => !string.IsNullOrEmpty(x.TaxCode));

        RuleFor(x => x.Description)
            .MaximumLength(5000).WithMessage("Mô tả không được vượt quá 5000 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Description));
    }
}

public class UpdateCompanyRequestValidator : AbstractValidator<UpdateCompanyRequest>
{
    public UpdateCompanyRequestValidator()
    {
        RuleFor(x => x.Name)
            .MinimumLength(2).WithMessage("Tên công ty phải có ít nhất 2 ký tự.")
            .MaximumLength(200).WithMessage("Tên công ty không được vượt quá 200 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Name));

        RuleFor(x => x.ContactEmail)
            .EmailAddress().WithMessage("Email liên hệ không hợp lệ.")
            .When(x => !string.IsNullOrEmpty(x.ContactEmail));

        RuleFor(x => x.Website)
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _))
            .WithMessage("Website phải là URL hợp lệ (bắt đầu bằng http:// hoặc https://).")
            .When(x => !string.IsNullOrEmpty(x.Website));

        RuleFor(x => x.TaxCode)
            .Matches(@"^\d{10,13}$").WithMessage("Mã số thuế phải có 10-13 chữ số.")
            .When(x => !string.IsNullOrEmpty(x.TaxCode));

        RuleFor(x => x.Description)
            .MaximumLength(5000).WithMessage("Mô tả không được vượt quá 5000 ký tự.")
            .When(x => !string.IsNullOrEmpty(x.Description));
    }
}

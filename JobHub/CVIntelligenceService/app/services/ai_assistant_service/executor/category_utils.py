# app/services/ai_assistant_service/executor/category_utils.py
"""
Chuẩn hóa category ngành nghề công việc.
"""

_VALID_CATEGORIES = [
    "Software Development",
    "Frontend Development",
    "Backend Development",
    "Fullstack Development",
    "Mobile Development",
    "DevOps & Cloud",
    "Data Engineering",
    "Data Science & AI",
    "Cybersecurity",
    "QA & Testing",
    "UI/UX Design",
    "Product Management",
    "Business Analysis",
    "ERP & Enterprise Systems",
    "Network & Sysadmin",
    "IT Support",
    "Game Development",
    "Blockchain & Web3",
    "Embedded & IoT",
    "Engineering",
    "Marketing",
    "Sales",
    "Other"
]

_CATEGORY_MAPPING = {
    "lập trình": "Software Development",
    "phần mềm": "Software Development",
    "software": "Software Development",
    "frontend": "Frontend Development",
    "giao diện": "Frontend Development",
    "backend": "Backend Development",
    "fullstack": "Fullstack Development",
    "mobile": "Mobile Development",
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "devops": "DevOps & Cloud",
    "cloud": "DevOps & Cloud",
    "data engineer": "Data Engineering",
    "dữ liệu": "Data Engineering",
    "data science": "Data Science & AI",
    "trí tuệ nhân tạo": "Data Science & AI",
    "ai": "Data Science & AI",
    "machine learning": "Data Science & AI",
    "an ninh mạng": "Cybersecurity",
    "cybersecurity": "Cybersecurity",
    "bảo mật": "Cybersecurity",
    "qa": "QA & Testing",
    "qc": "QA & Testing",
    "testing": "QA & Testing",
    "kiểm thử": "QA & Testing",
    "ui/ux": "UI/UX Design",
    "design": "UI/UX Design",
    "thiết kế": "UI/UX Design",
    "product manager": "Product Management",
    "quản trị sản phẩm": "Product Management",
    "ba": "Business Analysis",
    "business analyst": "Business Analysis",
    "erp": "ERP & Enterprise Systems",
    "sap": "ERP & Enterprise Systems",
    "network": "Network & Sysadmin",
    "hệ thống": "Network & Sysadmin",
    "system admin": "Network & Sysadmin",
    "support": "IT Support",
    "helpdesk": "IT Support",
    "game": "Game Development",
    "web3": "Blockchain & Web3",
    "blockchain": "Blockchain & Web3",
    "embedded": "Embedded & IoT",
    "iot": "Embedded & IoT",
    "nhúng": "Embedded & IoT",
    "kỹ thuật": "Engineering",
    "công nghệ": "Engineering",
    "marketing": "Marketing",
    "tiếp thị": "Marketing",
    "sales": "Sales",
    "kinh doanh": "Sales",
    "bán hàng": "Sales"
}


def normalize_category(category_input: str) -> str:
    """Chuẩn hóa category nhập vào về một trong các giá trị của _VALID_CATEGORIES."""
    if not category_input:
        return "Other"

    val = category_input.strip()
    # Nếu đã khớp chính xác
    if val in _VALID_CATEGORIES:
        return val

    val_lower = val.lower()
    # So khớp chính xác lowercase
    for cat in _VALID_CATEGORIES:
        if val_lower == cat.lower():
            return cat

    # Tìm kiếm theo từ khóa mapping
    for kw, target in _CATEGORY_MAPPING.items():
        if kw in val_lower:
            return target

    return "Other"

import os
import sys
import random
import shutil

# Configure output encoding for console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Make sure we can import from backend
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import generate_pdf_resumes
    from generate_pdf_resumes import (
        generate_candidate_profile,
        generate_pdf_cv,
        generate_pdf_cv_two_column,
        generate_pdf_cv_template_3,
        generate_pdf_cv_template_4,
        generate_pdf_cv_template_5,
        generate_pdf_cv_template_6,
        ADDRESSES,
        FIRST_NAMES,
        MIDDLE_NAMES,
        LAST_NAMES,
        make_slug
    )
except ImportError as e:
    print(f"[Error] Failed to import from generate_pdf_resumes.py: {e}")
    sys.exit(1)

# Dynamically inject Backend PHP data pools into generate_pdf_resumes
generate_pdf_resumes.SPECIALTIES["Backend PHP"] = {
    "title": "PHP Developer",
    "skills": [
        {"category": "Ngôn ngữ & Core", "items": ["PHP 8.x (OOP, MVC)", "Clean Architecture & SOLID", "Design Patterns", "Clean Code & PSR Standards"]},
        {"category": "Frameworks & ORM", "items": ["Laravel Framework (Eloquent ORM)", "Symfony Framework", "Laravel Nova / Orchid", "RESTful API / GraphQL"]},
        {"category": "Database & Ops", "items": ["MySQL / MariaDB", "Redis (Cache & Queue)", "Docker & Docker Compose", "CI/CD (GitHub Actions)"]}
    ],
    "projects": [
        {"name": "E-Commerce Core Solution", "description": "Thiết kế và xây dựng cổng API cho sàn thương mại điện tử chuyên nghiệp sử dụng Laravel 10. Sử dụng Eloquent ORM và Redis Cache giúp tăng tốc độ tải trang sản phẩm và tích hợp cổng thanh toán Momo, VNPAY.", "tags": ["Laravel", "MySQL", "Redis", "REST API"]},
        {"name": "Enterprise CRM Backend", "description": "Xây dựng cổng thông tin quản lý quan hệ khách hàng tập trung với cơ chế phân quyền RBAC và xây dựng báo cáo động phức tạp.", "tags": ["PHP 8", "Laravel", "MySQL", "Docker"]}
    ],
    "experiences": [
        {"position": "PHP Developer", "bullets": [
            "Phát triển hơn 30 RESTful API hiệu năng cao bằng Laravel Framework.",
            "Tối ưu hóa các truy vấn SQL thông qua Eloquent ORM, giảm 40% thời gian phản hồi hệ thống.",
            "Viết các bài kiểm thử tự động sử dụng PHPUnit để đảm bảo tính ổn định của mã nguồn."
        ]},
        {"position": "Senior PHP Developer", "bullets": [
            "Tái cấu trúc mã nguồn cũ sang kiến trúc Clean Architecture giúp hệ thống dễ bảo trì và mở rộng.",
            "Thiết lập hệ thống hàng đợi Redis queue xử lý bất đồng bộ các tác vụ nặng gửi mail, báo cáo.",
            "Dẫn dắt đội ngũ kỹ sư Junior viết code chuẩn PSR và review code hàng tuần."
        ]}
    ]
}

generate_pdf_resumes.SUMMARIES["Backend PHP"] = [
    "Kỹ sư Backend PHP với hơn 5 năm kinh nghiệm chuyên sâu thiết kế và vận hành các hệ thống web quy mô lớn sử dụng PHP và Laravel. Đam mê xây dựng kiến trúc backend sạch, tối ưu hóa cơ sở dữ liệu lớn và thiết lập hệ thống queue hiệu năng cao. Luôn chú trọng viết code chuẩn PSR và bảo mật hệ thống.",
    "Lập trình viên backend PHP năng động có tư duy logic vững vàng và am hiểu sâu sắc về Laravel. Có kinh nghiệm xây dựng RESTful API và làm việc với MySQL, Redis. Mong muốn được học hỏi và cống hiến để cùng đội ngũ phát triển các giải pháp backend ổn định."
]

generate_pdf_resumes.CERTIFICATES_POOL["Backend PHP"] = [
    {"date": "08/2025", "title": "Laravel Certified Developer - Laravel Certification"},
    {"date": "02/2025", "title": "AWS Certified Developer - Associate"},
    {"date": "04/2026", "title": "TOEIC 800 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
]

generate_pdf_resumes.REFERENCES_POOL["Backend PHP"] = [
    "Nguyễn Văn An - Technical Lead tại FPT Software - SĐT: 0987654321 - Email: annv@fsoft.com.vn",
    "Phạm Văn Bình - Engineering Manager tại VNG Corporation - Email: binhpv@vng.com.vn"
]

def build_unique_names(count=50):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP"]:
        folder_path = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", folder)
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                if f.startswith("cv_") and f.endswith(".pdf"):
                    parts = f[3:-4].split("_")
                    if len(parts) >= 3:
                        existing_slugs.add("_".join(parts[:3]))
                        
    # 2. Build all combinations
    names_pool = []
    for f in FIRST_NAMES:
        for m in MIDDLE_NAMES:
            for l in LAST_NAMES:
                names_pool.append((f, m, l))
                
    # 3. Shuffle with seed 2031 (fresh diversity and uniqueness)
    random.seed(2031)
    random.shuffle(names_pool)
    
    # 4. Filter out any name that has a slug in existing_slugs
    selected_names = []
    for n in names_pool:
        full_name = f"{n[0]} {n[1]} {n[2]}"
        slug = make_slug(full_name).replace(".", "_")
        if slug not in existing_slugs:
            selected_names.append(full_name)
            if len(selected_names) == count:
                break
                
    return selected_names

def main():
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV PHP")
    
    # Get unique names first
    unique_names = build_unique_names(50)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV PHP folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 50 CV BACKEND PHP (LARAVEL) TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(50):
        loc = "Hà Nội" if j < 25 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        configs.append({
            "specialty": "Backend PHP",
            "location": loc,
            "level": level,
            "template": curr_template
        })
            
    success = 0
    for i in range(50):
        # 1. Unique Name
        full_name = unique_names[i]
        
        # 2. Config
        cfg = configs[i]
        specialty = cfg["specialty"]
        loc = cfg["location"]
        level = cfg["level"]
        curr_template = cfg["template"]
        
        # 3. Experience Years based on level
        exp_years = 0
        if level == "FRESHER": exp_years = random.choice([0, 1])
        elif level == "JUNIOR": exp_years = random.randint(1, 2)
        elif level == "MIDDLE": exp_years = random.randint(3, 4)
        elif level == "SENIOR": exp_years = random.randint(5, 7)
        elif level == "LEADER": exp_years = random.randint(7, 9)
        elif level == "MANAGER": exp_years = random.randint(9, 12)
        
        # 4. Generate Candidate Profile
        profile = generate_candidate_profile(full_name, specialty, level, exp_years, location=loc)
        
        # Set exact specialty text to "Backend PHP (Laravel)"
        profile["specialty"] = "Backend PHP (Laravel)"
        profile["title"] = "PHP Laravel Developer"
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "backend_php"
        file_name = f"cv_{name_slug}_{spec_slug}_{level.lower()}.pdf"
        file_path = os.path.join(output_dir, file_name)
        
        # 6. Generate PDF based on template choice (1 to 6)
        try:
            if curr_template == 1:
                generate_pdf_cv(file_path, profile)
            elif curr_template == 2:
                generate_pdf_cv_two_column(file_path, profile)
            elif curr_template == 3:
                generate_pdf_cv_template_3(file_path, profile)
            elif curr_template == 4:
                generate_pdf_cv_template_4(file_path, profile)
            elif curr_template == 5:
                generate_pdf_cv_template_5(file_path, profile)
            elif curr_template == 6:
                generate_pdf_cv_template_6(file_path, profile)
                
            success += 1
            print(f"[{success}/50] Đã tạo Mẫu {curr_template} | {loc} | {profile['specialty']} | Level: {level} -> {file_name}")
        except Exception as e:
            print(f"❌ Lỗi khi tạo file {file_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ HOÀN THÀNH! Đã tạo thành công {success}/50 CV trong thư mục {output_dir}")

if __name__ == "__main__":
    main()

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

def build_unique_names(count=100):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++", "CV ReactJS", "CV Angular", "CV VueJS", "CV fullstack"]:
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
                
    # 3. Shuffle with seed 2060 (fresh diversity and uniqueness)
    random.seed(2060)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV fullstack")
    
    # Get unique names first
    unique_names = build_unique_names(100)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV fullstack folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 100 CV FULLSTACK TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    frontends = {
        "ReactJS": ["ReactJS", "Redux Toolkit", "React Query", "Tailwind CSS"],
        "Angular": ["Angular Framework", "RxJS", "NgRx State Management", "Angular Material"],
        "VueJS": ["Vue.js 3", "Pinia Store", "Vue Router", "Element Plus"]
    }
    
    backends = {
        "Node.js": ["Node.js (NestJS / Express)", "MongoDB", "REST API / WebSockets"],
        ".NET": ["C# & ASP.NET Core API", "SQL Server / EF Core", "Microservices & RabbitMQ"],
        "Java": ["Java & Spring Boot Framework", "Hibernate & JPA", "MySQL / Redis"],
        "Python": ["Python (FastAPI / Django)", "PostgreSQL", "Celery & Redis queue"],
        "PHP": ["PHP 8 & Laravel Framework", "Eloquent ORM", "MySQL / Redis"]
    }
    
    configs = []
    for j in range(100):
        loc = "Hà Nội" if j < 50 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        
        # Choose random Frontend and Backend technologies
        fe = random.choice(list(frontends.keys()))
        be = random.choice(list(backends.keys()))
        
        configs.append({
            "fe": fe,
            "be": be,
            "location": loc,
            "level": level,
            "template": curr_template
        })
            
    success = 0
    for i in range(100):
        # 1. Unique Name
        full_name = unique_names[i]
        
        # 2. Config
        cfg = configs[i]
        fe = cfg["fe"]
        be = cfg["be"]
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
        
        # 4. Dynamically configure Backend C pool in generate_pdf_resumes with custom fullstack details
        generate_pdf_resumes.SPECIALTIES["Backend C"] = {
            "title": f"Fullstack Developer ({fe} & {be})",
            "skills": [
                {"category": "Frontend Tech Stack", "items": frontends[fe] + ["HTML5 & CSS3 (Sass)", "Responsive Web Design"]},
                {"category": "Backend Tech Stack", "items": backends[be] + ["RESTful API & Security", "Database Modeling"]},
                {"category": "Tools & DevOps", "items": ["Git & GitHub", "Docker Containers", "CI/CD Pipelines (GitHub Actions)", "Linux / AWS"]}
            ],
            "projects": [
                {
                    "name": "Integrated E-Commerce Platform", 
                    "description": f"Thiết kế và xây dựng giải pháp thương mại điện tử trọn gói (Fullstack). Phát triển giao diện người dùng tương tác cao bằng {fe}, quản lý state hiệu quả. Xây dựng hệ thống REST API backend hiệu năng cao bằng {be}, tích hợp cổng thanh toán trực tuyến và tối ưu hóa cơ sở dữ liệu.", 
                    "tags": [fe, be, "Docker", "REST API"]
                },
                {
                    "name": "Enterprise Project Management System", 
                    "description": f"Phát triển ứng dụng quản lý dự án nội bộ dành cho doanh nghiệp. Sử dụng {fe} để thiết kế các bảng điều khiển trực quan (BI Dashboards), kéo thả quản lý Task. Sử dụng {be} để xử lý phân quyền người dùng (RBAC), đồng bộ dữ liệu thời gian thực qua WebSockets.", 
                    "tags": [fe, be, "WebSockets", "JWT"]
                }
            ],
            "experiences": [
                {"position": "Fullstack Developer", "bullets": [
                    f"Phát triển giao diện web responsive tương tác cao sử dụng thư viện/framework {fe}.",
                    f"Xây dựng và tối ưu hóa các RESTful API backend chất lượng cao sử dụng công nghệ {be}.",
                    "Thiết kế cấu trúc cơ sở dữ liệu hiệu năng tốt và viết các kịch bản kiểm thử tự động.",
                    "Làm việc theo mô hình Agile/Scrum và phối hợp chặt chẽ với đội ngũ phát triển sản phẩm."
                ]},
                {"position": "Senior Fullstack Developer", "bullets": [
                    f"Thiết kế kiến trúc hệ thống tổng thể cho giải pháp web fullstack sử dụng {fe} ở client và {be} ở server.",
                    "Tối ưu hóa hiệu năng render phía client và cấu trúc truy vấn phía server giúp giảm 40% thời gian tải trang.",
                    "Triển khai tự động hóa quy trình CI/CD pipelines, container hóa ứng dụng sử dụng Docker.",
                    "Dẫn dắt kỹ thuật, tổ chức review code hàng tuần và hỗ trợ định hướng công nghệ cho các junior."
                ]}
            ]
        }
        
        generate_pdf_resumes.SUMMARIES["Backend C"] = [
            f"Kỹ sư Fullstack giàu kinh nghiệm với thế mạnh chuyên sâu về phát triển giao diện {fe} và xây dựng kiến trúc backend bằng {be}. Có hơn 5 năm kinh nghiệm thực chiến phát triển các hệ thống web quy mô lớn, tối ưu hóa toàn bộ luồng dữ liệu từ client đến server và thiết lập quy trình triển khai tự động CI/CD.",
            f"Lập trình viên Fullstack năng động có khả năng làm chủ cả frontend {fe} và backend {be}. Có tư duy logic tốt, kỹ năng giải quyết vấn đề nhanh nhạy và am hiểu các quy chuẩn viết code sạch. Luôn mong muốn học hỏi và nâng cao trình độ kỹ thuật."
        ]
        
        generate_pdf_resumes.CERTIFICATES_POOL["Backend C"] = [
            {"date": "08/2025", "title": "Full Stack Web Developer Certification"},
            {"date": "02/2025", "title": "AWS Certified Developer - Associate"},
            {"date": "04/2026", "title": "TOEIC 830 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
        ]
        
        generate_pdf_resumes.REFERENCES_POOL["Backend C"] = [
            "Nguyễn Văn Dũng - Chief Technology Officer tại VNG Corporation - SĐT: 0987654321 - Email: dungnv@vng.com.vn",
            "Trần Thị Lan - Engineering Manager tại FPT Software - Email: lantt@fsoft.com.vn"
        ]
        
        # 5. Generate Candidate Profile using the dynamically updated "Backend C" specialty
        profile = generate_candidate_profile(full_name, "Backend C", level, exp_years, location=loc)
        
        # Override specialty text and title in profile for presentation
        profile["specialty"] = f"Fullstack Developer ({fe} & {be})"
        profile["title"] = f"Fullstack Developer ({fe} & {be})"
        
        # Adjust experiences' position titles to match
        for exp in profile["experiences"]:
            pos = exp["position"]
            if "Fullstack Developer" in pos:
                pass
            elif "Developer" in pos:
                exp["position"] = pos.replace("Developer", f"Fullstack Developer ({fe} & {be})")
        
        # 6. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "fullstack"
        file_name = f"cv_{name_slug}_{spec_slug}_{level.lower()}.pdf"
        file_path = os.path.join(output_dir, file_name)
        
        # 7. Generate PDF based on template choice (1 to 6)
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
            print(f"[{success}/100] Đã tạo Mẫu {curr_template} | {loc} | {profile['specialty']} | Level: {level} -> {file_name}")
        except Exception as e:
            print(f"❌ Lỗi khi tạo file {file_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ HOÀN THÀNH! Đã tạo thành công {success}/100 CV trong thư mục {output_dir}")

if __name__ == "__main__":
    main()

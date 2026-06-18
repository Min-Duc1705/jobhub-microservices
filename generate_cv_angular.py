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

# Dynamically inject Frontend Angular data pools into generate_pdf_resumes
generate_pdf_resumes.SPECIALTIES["Frontend Angular"] = {
    "title": "Angular Developer",
    "skills": [
        {"category": "Core & Language", "items": ["TypeScript, JavaScript (ES6+)", "HTML5 & CSS3 (Sass/SCSS)", "RxJS (Reactive Extensions)", "Responsive Web Design"]},
        {"category": "Angular Core", "items": ["Angular Framework (v16/17/18)", "Angular CLI & Architecture", "State Management (NgRx, Akita)", "Angular Router & Route Guards"]},
        {"category": "Tools & Testing", "items": ["Angular Material / PrimeNG", "RxJS Operators", "Karma & Jasmine (Unit Testing)", "Vite / Webpack / Git"]}
    ],
    "projects": [
        {"name": "Enterprise Admin Portal", "description": "Phát triển cổng thông tin quản trị doanh nghiệp quy mô lớn bằng Angular 16 và NgRx. Thiết kế kiến trúc component tối ưu và xử lý các luồng dữ liệu bất đồng bộ phức tạp sử dụng RxJS.", "tags": ["Angular", "NgRx", "RxJS", "TypeScript"]},
        {"name": "Real-Time Data Dashboard", "description": "Xây dựng dashboard giám sát dữ liệu thời gian thực tích hợp WebSockets, tối ưu hóa Change Detection Strategy (OnPush) để đảm bảo tốc độ phản hồi giao diện mượt mà dưới 50ms.", "tags": ["Angular", "RxJS", "WebSockets", "Angular Material"]}
    ],
    "experiences": [
        {"position": "Angular Developer", "bullets": [
            "Phát triển các component giao diện người dùng responsive sử dụng Angular và TypeScript.",
            "Tích hợp và xử lý API RESTful thông qua HttpClient của Angular, sử dụng RxJS để quản lý luồng dữ liệu.",
            "Thực hiện viết unit test cho các component và service sử dụng Karma và Jasmine."
        ]},
        {"position": "Senior Angular Developer", "bullets": [
            "Thiết kế kiến trúc dự án Angular lớn dạng Monorepo sử dụng Nx Dev Tools.",
            "Tối ưu hóa hiệu năng ứng dụng thông qua Lazy Loading modules, tối ưu hóa bundle size và thiết lập cơ chế OnPush Change Detection.",
            "Xây dựng và đóng gói bộ thư viện UI component dùng chung cho doanh nghiệp."
        ]}
    ]
}

generate_pdf_resumes.SUMMARIES["Frontend Angular"] = [
    "Kỹ sư Frontend chuyên sâu về Angular với hơn 5 năm kinh nghiệm xây dựng các ứng dụng doanh nghiệp (Enterprise Apps) quy mô lớn. Am hiểu sâu sắc về RxJS, lập trình phản ứng (Reactive Programming) và quản lý trạng thái bằng NgRx. Đam mê tối ưu hóa hiệu năng và kiến trúc phần mềm sạch.",
    "Lập trình viên Angular có kỹ năng lập trình TypeScript tốt và am hiểu về RxJS. Có kinh nghiệm xây dựng các tính năng tương tác người dùng phức tạp và tối ưu giao diện responsive. Sẵn sàng học hỏi và cống hiến cho nhóm."
]

generate_pdf_resumes.CERTIFICATES_POOL["Frontend Angular"] = [
    {"date": "08/2025", "title": "Angular Certified Developer - Angular Training"},
    {"date": "02/2025", "title": "RxJS Professional Certification - RxJS Academy"},
    {"date": "04/2026", "title": "TOEIC 820 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
]

generate_pdf_resumes.REFERENCES_POOL["Frontend Angular"] = [
    "Phạm Minh Hoàng - Frontend Lead tại FPT Software - SĐT: 0987654321 - Email: hoangpm@fsoft.com.vn",
    "Nguyễn Văn Tiến - Engineering Manager tại VNG Corporation - Email: tiennv@vng.com.vn"
]

def build_unique_names(count=50):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++", "CV ReactJS", "CV Angular"]:
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
                
    # 3. Shuffle with seed 2045 (fresh diversity and uniqueness)
    random.seed(2045)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV Angular")
    
    # Get unique names first
    unique_names = build_unique_names(50)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV Angular folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 50 CV ANGULAR TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(50):
        loc = "Hà Nội" if j < 25 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        configs.append({
            "specialty": "Frontend Angular",
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
        
        # Set exact specialty text and title
        profile["specialty"] = "Frontend Angular"
        profile["title"] = "Angular Developer"
        
        # Adjust experiences' position titles to match
        for exp in profile["experiences"]:
            pos = exp["position"]
            if "Angular Developer" in pos:
                pass
            elif "Developer" in pos:
                exp["position"] = pos.replace("Developer", "Angular Developer")
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "frontend_angular"
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

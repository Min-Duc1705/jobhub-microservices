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

# Ensure Frontend React data is configured (just in case)
if "Frontend React" not in generate_pdf_resumes.SPECIALTIES:
    generate_pdf_resumes.SPECIALTIES["Frontend React"] = {
        "title": "React Developer",
        "skills": [
            {"category": "Core & Language", "items": ["JavaScript (ES6+), TypeScript", "HTML5 & CSS3 (Sass/SCSS)", "Responsive Web Design", "DOM Manipulation"]},
            {"category": "Framework & State", "items": ["ReactJS (Hooks, Context API)", "Next.js (SSR, SSG)", "Redux Toolkit / Zustand", "React Query / Axios"]},
            {"category": "Styling & Tools", "items": ["Tailwind CSS / CSS Modules", "MUI / Ant Design", "Jest & React Testing Library", "Webpack / Vite / Git"]}
        ],
        "projects": [
            {"name": "E-Commerce Storefront", "description": "Xây dựng giao diện ứng dụng thương mại điện tử responsive hoàn chỉnh bằng ReactJS, Next.js và Tailwind CSS. Tối ưu SEO, cải thiện chỉ số Core Web Vitals (FCP, LCP) và quản lý giỏ hàng bằng Redux Toolkit.", "tags": ["ReactJS", "Next.js", "Tailwind CSS", "Redux"]},
            {"name": "Task Management Dashboard", "description": "Thiết kế bảng quản trị công việc thông minh hỗ trợ kéo thả trực quan và đồng bộ dữ liệu thời gian thực thông qua REST API.", "tags": ["ReactJS", "TypeScript", "Ant Design", "Vite"]}
        ],
        "experiences": [
            {"position": "React Developer", "bullets": [
                "Phát triển các component dùng chung chất lượng cao bằng ReactJS và TypeScript.",
                "Tích hợp RESTful API hiệu quả và tối ưu hóa trải nghiệm người dùng trên môi trường di động.",
                "Thực hiện viết unit test cho các component cốt lõi."
            ]},
            {"position": "Senior React Developer", "bullets": [
                "Thiết kế kiến trúc ứng dụng ReactJS lớn sử dụng Next.js giúp tối ưu hóa SEO và Server-Side Rendering.",
                "Tối ưu hóa hiệu năng render (memoization, lazy loading) giúp giảm 30% thời gian tải trang.",
                "Dẫn dắt và định hướng công nghệ cho các thành viên trong nhóm phát triển frontend."
            ]}
        ]
    }

if "Frontend React" not in generate_pdf_resumes.SUMMARIES:
    generate_pdf_resumes.SUMMARIES["Frontend React"] = [
        "Kỹ sư Frontend chuyên sâu về ReactJS và Next.js với hơn 5 năm kinh nghiệm xây dựng các ứng dụng web phức tạp, responsive và tối ưu hiệu năng. Đam mê thiết kế giao diện tinh tế, trải nghiệm người dùng mượt mà và viết mã nguồn sạch.",
        "Lập trình viên ReactJS trẻ tuổi, đam mê công nghệ và có tư duy thiết kế tốt. Có kinh nghiệm làm việc với JavaScript, TypeScript, Tailwind CSS và REST API. Mong muốn học hỏi và đồng hành cùng dự án."
    ]

if "Frontend React" not in generate_pdf_resumes.CERTIFICATES_POOL:
    generate_pdf_resumes.CERTIFICATES_POOL["Frontend React"] = [
        {"date": "08/2025", "title": "Meta Front-End Developer Professional Certificate"},
        {"date": "02/2025", "title": "AWS Certified Cloud Practitioner"},
        {"date": "04/2026", "title": "TOEIC 800 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
    ]

if "Frontend React" not in generate_pdf_resumes.REFERENCES_POOL:
    generate_pdf_resumes.REFERENCES_POOL["Frontend React"] = [
        "Lê Minh Hùng - Frontend Lead tại VNG Corporation - SĐT: 0912345678 - Email: hunglm@vng.com.vn",
        "Nguyễn Thị Hương - Engineering Manager tại KMS Technology - Email: huongnt@kms-technology.com"
    ]

def build_unique_names(count=50):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++", "CV ReactJS"]:
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
                
    # 3. Shuffle with seed 2040 (fresh diversity and uniqueness)
    random.seed(2040)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV ReactJS")
    
    # Get unique names first
    unique_names = build_unique_names(50)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV ReactJS folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 50 CV REACTJS TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(50):
        loc = "Hà Nội" if j < 25 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        configs.append({
            "specialty": "Frontend React",
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
        profile["specialty"] = "Frontend ReactJS"
        profile["title"] = "ReactJS Developer"
        
        # Adjust experiences' position titles to match
        for exp in profile["experiences"]:
            pos = exp["position"]
            if "React Developer" in pos:
                exp["position"] = pos.replace("React Developer", "ReactJS Developer")
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "frontend_react"
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

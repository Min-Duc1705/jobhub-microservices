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

# Dynamically inject Frontend Vue data pools into generate_pdf_resumes
generate_pdf_resumes.SPECIALTIES["Frontend Vue"] = {
    "title": "VueJS Developer",
    "skills": [
        {"category": "Core & Language", "items": ["JavaScript (ES6+), TypeScript", "HTML5 & CSS3 (Sass/SCSS)", "Responsive Web Design", "DOM Manipulation"]},
        {"category": "Vue Core", "items": ["Vue.js (v2/v3, Composition API)", "Vue CLI & Vite", "State Management (Pinia, Vuex)", "Vue Router"]},
        {"category": "Tools & Testing", "items": ["Element Plus / Vuetify / PrimeVue", "Tailwind CSS", "Vitest & Cypress (Testing)", "Webpack / Vite / Git"]}
    ],
    "projects": [
        {"name": "Real-Time Collaboration Tool", "description": "Phát triển công cụ cộng tác trực tuyến thời gian thực bằng Vue 3, Pinia và WebSockets. Tối ưu hóa hiệu năng render thông qua virtual scrolling và custom directives.", "tags": ["Vue 3", "Pinia", "WebSockets", "TypeScript"]},
        {"name": "E-Commerce Admin Panel", "description": "Xây dựng trang dashboard quản trị bán hàng đa kênh responsive sử dụng Vue 3, Composition API và Element Plus, tích hợp các biểu đồ phân tích trực quan.", "tags": ["Vue 3", "Element Plus", "Vite", "Chart.js"]}
    ],
    "experiences": [
        {"position": "VueJS Developer", "bullets": [
            "Phát triển các component giao diện người dùng responsive sử dụng Vue.js và JavaScript/TypeScript.",
            "Tích hợp RESTful API hiệu quả và quản lý trạng thái cục bộ sử dụng Pinia/Vuex.",
            "Viết unit test cho các component cơ bản bằng Vitest."
        ]},
        {"position": "Senior VueJS Developer", "bullets": [
            "Thiết kế kiến trúc dự án Vue 3 lớn sử dụng Composition API và Vite giúp tăng tốc độ phát triển.",
            "Tối ưu hóa bundle size và lazy loading cho ứng dụng Single Page Application (SPA) Vue.js.",
            "Định hướng phát triển và review code cho nhóm frontend."
        ]}
    ]
}

generate_pdf_resumes.SUMMARIES["Frontend Vue"] = [
    "Kỹ sư Frontend chuyên sâu về Vue.js với hơn 5 năm kinh nghiệm xây dựng các hệ thống giao diện ứng dụng web hiện đại và hiệu năng cao. Am hiểu sâu sắc về Vue 3 (Composition API), Pinia và hệ sinh thái Vite. Đam mê thiết kế UI/UX tinh tế và tối ưu hóa trải nghiệm khách hàng.",
    "Lập trình viên Vue.js năng động, am hiểu về lập trình web hiện đại và TypeScript. Có kinh nghiệm xây dựng giao diện responsive và tương tác mượt mà. Sẵn sàng học hỏi công nghệ mới và đóng góp cho sự phát triển của đội ngũ."
]

generate_pdf_resumes.CERTIFICATES_POOL["Frontend Vue"] = [
    {"date": "08/2025", "title": "Vue.js Certified Developer Professional - Vue School"},
    {"date": "02/2025", "title": "Advanced Frontend Web Development - Coursera"},
    {"date": "04/2026", "title": "TOEIC 810 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
]

generate_pdf_resumes.REFERENCES_POOL["Frontend Vue"] = [
    "Lê Văn Thành - Frontend Lead tại Tiki Corp - SĐT: 0989999888 - Email: thanh.le@tiki.vn",
    "Nguyễn Thị Mai - Engineering Manager tại VNG Corporation - Email: maint@vng.com.vn"
]

def build_unique_names(count=50):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++", "CV ReactJS", "CV Angular", "CV VueJS"]:
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
                
    # 3. Shuffle with seed 2050 (fresh diversity and uniqueness)
    random.seed(2050)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV VueJS")
    
    # Get unique names first
    unique_names = build_unique_names(50)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV VueJS folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 50 CV VUEJS TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(50):
        loc = "Hà Nội" if j < 25 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        configs.append({
            "specialty": "Frontend Vue",
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
        profile["specialty"] = "Frontend VueJS"
        profile["title"] = "VueJS Developer"
        
        # Adjust experiences' position titles to match
        for exp in profile["experiences"]:
            pos = exp["position"]
            if "VueJS Developer" in pos:
                pass
            elif "Developer" in pos:
                exp["position"] = pos.replace("Developer", "VueJS Developer")
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "frontend_vue"
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

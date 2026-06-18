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

# Dynamically inject QA Automation / Tester data pools into generate_pdf_resumes
generate_pdf_resumes.SPECIALTIES["QA Automation"] = {
    "title": "QA Engineer",
    "skills": [
        {"category": "Testing Core", "items": ["Manual Testing & Test Case Design", "Automation Testing (Selenium, Playwright)", "API Testing (Postman, SoapUI)", "Bug Tracking (Jira, Redmine)"]},
        {"category": "Automation & Tools", "items": ["TestNG / JUnit / PyTest", "CI/CD (Jenkins, GitHub Actions)", "SQL & Database Testing", "Performance Testing (JMeter)"]},
        {"category": "Soft Skills", "items": ["Analytical Thinking", "Communication & Teamwork", "Agile / Scrum", "Attention to Detail"]}
    ],
    "projects": [
        {"name": "E-Commerce Automation Testing Suite", "description": "Xây dựng khung kiểm thử tự động (Automation Framework) toàn diện cho sàn thương mại điện tử sử dụng Playwright và Python. Thiết kế các kịch bản kiểm thử API và UI end-to-end, tích hợp vào CI/CD pipeline giúp giảm 70% thời gian kiểm thử hồi quy.", "tags": ["Playwright", "Python", "API Testing", "Jira"]},
        {"name": "Enterprise App Manual Testing", "description": "Thiết kế kế hoạch kiểm thử (Test Plan) và hơn 500 ca kiểm thử (Test Cases) chi tiết cho ứng dụng quản trị doanh nghiệp lớn. Thực hiện kiểm thử chức năng (Functional), hiệu năng (Performance) và bảo mật cơ bản, phát hiện hơn 120 lỗi nghiêm trọng trước ngày release.", "tags": ["Manual Testing", "Test Case Design", "Postman", "SQL"]}
    ],
    "experiences": [
        {"position": "QA Engineer", "bullets": [
            "Phân tích yêu cầu nghiệp vụ và viết các ca kiểm thử (Test Cases), kịch bản kiểm thử (Test Scripts).",
            "Thực hiện kiểm thử chức năng (Functional Testing), kiểm thử hồi quy (Regression Testing) trên môi trường web và mobile.",
            "Thực hiện kiểm thử API bằng Postman và lập báo cáo lỗi (Bug Reports) chi tiết trên Jira."
        ]},
        {"position": "Senior QA Engineer", "bullets": [
            "Thiết kế kế hoạch kiểm thử (Test Plan) tổng thể và lựa chọn giải pháp kiểm thử tự động phù hợp với dự án.",
            "Xây dựng và phát triển khung kiểm thử tự động (Automation Framework) từ đầu sử dụng Selenium Webdriver hoặc Cypress.",
            "Quản lý và dẫn dắt đội ngũ QA/QC, phân công công việc, đánh giá chất lượng sản phẩm và tổ chức các buổi đào tạo kỹ thuật nội bộ."
        ]}
    ]
}

generate_pdf_resumes.SUMMARIES["QA Automation"] = [
    "Kỹ sư kiểm thử phần mềm (QA/QC) với hơn 5 năm kinh nghiệm chuyên sâu trong cả kiểm thử thủ công (Manual Testing) và kiểm thử tự động (Automation Testing). Có khả năng thiết kế ca kiểm thử thông minh, phát hiện lỗi sâu sắc và xây dựng các khung tự động hóa hiệu năng cao. Luôn chú trọng nâng cao chất lượng sản phẩm và tối ưu hóa quy trình phát triển phần mềm.",
    "Chuyên viên kiểm thử phần mềm năng động, tỉ mỉ và có óc phân tích nhạy bén. Có kinh nghiệm viết tài liệu kiểm thử, thực hiện test case trên giao diện web/mobile và kiểm thử API bằng Postman. Sẵn sàng nghiên cứu các công nghệ kiểm thử tự động mới để gia tăng hiệu suất kiểm thử."
]

generate_pdf_resumes.CERTIFICATES_POOL["QA Automation"] = [
    {"date": "08/2025", "title": "ISTQB Certified Tester - Foundation Level (CTFL)"},
    {"date": "02/2025", "title": "Automation Test Specialist Certification"},
    {"date": "04/2026", "title": "TOEIC 800 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
]

generate_pdf_resumes.REFERENCES_POOL["QA Automation"] = [
    "Lê Minh Tuấn - QA Manager tại VNG Corporation - SĐT: 0987654321 - Email: tuanlm@vng.com.vn",
    "Trần Thị Hương - QC Leader tại FPT Software - Email: huongtt@fsoft.com.vn"
]

def build_unique_names(count=100):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++", "CV ReactJS", "CV Angular", "CV VueJS", "CV fullstack", "CV devops", "CV tester"]:
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
                
    # 3. Shuffle with seed 2080 (fresh diversity and uniqueness)
    random.seed(2080)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV tester")
    
    # Get unique names first
    unique_names = build_unique_names(100)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV tester folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 100 CV TESTER TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(100):
        loc = "Hà Nội" if j < 50 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        
        # Randomly choose one of the QA/Testing roles
        role_type = random.choice(["QA Automation Engineer", "Manual QA Engineer", "Software Testing Specialist"])
        
        configs.append({
            "specialty": "QA Automation",
            "location": loc,
            "level": level,
            "template": curr_template,
            "role_type": role_type
        })
            
    success = 0
    for i in range(100):
        # 1. Unique Name
        full_name = unique_names[i]
        
        # 2. Config
        cfg = configs[i]
        specialty = cfg["specialty"]
        loc = cfg["location"]
        level = cfg["level"]
        curr_template = cfg["template"]
        role_type = cfg["role_type"]
        
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
        profile["specialty"] = role_type
        profile["title"] = role_type
        
        # Adjust experiences' position titles to match
        for exp in profile["experiences"]:
            pos = exp["position"]
            if "QA Engineer" in pos:
                # e.g., "Senior QA Engineer" -> "Senior QA Automation Engineer"
                exp["position"] = pos.replace("QA Engineer", role_type)
            elif "Developer" in pos:
                exp["position"] = pos.replace("Developer", role_type)
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "tester"
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
            print(f"[{success}/100] Đã tạo Mẫu {curr_template} | {loc} | {profile['specialty']} | Level: {level} -> {file_name}")
        except Exception as e:
            print(f"❌ Lỗi khi tạo file {file_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ HOÀN THÀNH! Đã tạo thành công {success}/100 CV trong thư mục {output_dir}")

if __name__ == "__main__":
    main()

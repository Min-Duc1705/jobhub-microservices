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

# Dynamically inject Business Analyst data pools into generate_pdf_resumes
generate_pdf_resumes.SPECIALTIES["Business Analyst"] = {
    "title": "Business Analyst",
    "skills": [
        {"category": "Requirements Engineering", "items": ["Requirements Gathering", "SRS Documentation", "Use Case & User Story Specification", "Product Backlog Management"]},
        {"category": "Modeling & Tools", "items": ["UML Diagrams (Use Case, Sequence, Activity)", "BPMN & Flowcharts", "Figma / Balsamiq (Wireframing)", "Jira / Confluence"]},
        {"category": "Data & Analysis", "items": ["SQL & Relational Databases", "Data Flow Diagrams (DFD)", "Excel (Pivot, VLOOKUP)", "Power BI / Tableau"]},
        {"category": "Soft Skills", "items": ["Stakeholder Management", "Agile / Scrum Framework", "Effective Communication", "Analytical & Problem Solving"]}
    ],
    "projects": [
        {"name": "Core Banking System Upgrade Analysis", "description": "Khảo sát, thu thập và phân tích hơn 200 yêu cầu nghiệp vụ cho dự án nâng cấp hệ thống Core Banking. Thiết kế luồng quy trình (To-Be) nghiệp vụ thanh toán, chuyển khoản liên ngân hàng và đặc tả Use Case chi tiết giúp đội Dev phát triển chính xác 100%.", "tags": ["UML", "BPMN", "Core Banking", "Jira"]},
        {"name": "E-Commerce App Loyalty Program Integration", "description": "Chịu trách nhiệm phân tích luồng trải nghiệm khách hàng và thiết kế wireframe cho tính năng Loyalty Program trên Mobile App. Biên soạn tài liệu SRS, tài liệu hướng dẫn nghiệm thu (UAT) giúp nâng tỷ lệ giữ chân khách hàng thêm 25%.", "tags": ["Figma", "SRS", "User Stories", "UAT Testing"]}
    ],
    "experiences": [
        {"position": "Business Analyst", "bullets": [
            "Khảo sát, làm việc trực tiếp với khách hàng và các bên liên quan để làm rõ yêu cầu nghiệp vụ phần mềm.",
            "Biên soạn tài liệu đặc tả yêu cầu phần mềm (SRS), mô tả Use Case và các tài liệu nghiệp vụ liên quan.",
            "Thiết kế luồng quy trình (Workflow) bằng BPMN, xây dựng biểu đồ UML và phối hợp chặt chẽ với đội ngũ UI/UX thiết kế wireframe."
        ]},
        {"position": "Senior Business Analyst", "bullets": [
            "Dẫn dắt các buổi phân tích nghiệp vụ, quản lý phạm vi dự án (Scope Management) và đàm phán giải pháp với Stakeholders.",
            "Tối ưu hóa quy trình phân tích nghiệp vụ trong tổ chức, hỗ trợ Product Owner quản lý và sắp xếp thứ tự ưu tiên Product Backlog.",
            "Đào tạo kỹ năng phân tích nghiệp vụ và cố vấn cho các thành viên Business Analyst cấp dưới."
        ]}
    ]
}

generate_pdf_resumes.SUMMARIES["Business Analyst"] = [
    "Chuyên viên Phân tích Nghiệp vụ (Business Analyst) với hơn 5 năm kinh nghiệm làm việc trong các dự án phần mềm đa lĩnh vực (Tài chính, Bán lẻ, ERP). Có thế mạnh nổi trội trong việc làm rõ các yêu cầu phức tạp, cầu nối vững chắc giữa khách hàng và đội kỹ thuật nhằm tối ưu chất lượng giải pháp phần mềm.",
    "Business Analyst nhiệt huyết, có tư duy logic cao và kỹ năng giao tiếp xuất sắc. Thành thạo việc vẽ wireframe, thiết kế luồng quy trình BPMN, viết User Stories và tài liệu đặc tả SRS. Luôn mong muốn mang lại giá trị thực tiễn cao nhất cho khách hàng thông qua giải pháp phần mềm tối ưu."
]

generate_pdf_resumes.CERTIFICATES_POOL["Business Analyst"] = [
    {"date": "09/2025", "title": "Certified Business Analysis Professional (CBAP)"},
    {"date": "03/2025", "title": "Professional Scrum Product Owner I (PSPO I)"},
    {"date": "05/2026", "title": "TOEIC 850 - Chứng chỉ tiếng Anh chuyên nghiệp"}
]

generate_pdf_resumes.REFERENCES_POOL["Business Analyst"] = [
    "Nguyễn Minh Hùng - Product Director tại FPT Software - Email: hungnm@fsoft.com.vn",
    "Trần Thu Trang - PMO Lead tại OneMount Group - SĐT: 0912345678 - Email: trangtt@onemount.com"
]

def build_unique_names(count=100):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++", "CV ReactJS", "CV Angular", "CV VueJS", "CV fullstack", "CV devops", "CV tester", "CV BA"]:
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
                
    # 3. Shuffle with seed 3090 (fresh diversity and uniqueness for BA)
    random.seed(3090)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV BA")
    
    # Get unique names first
    unique_names = build_unique_names(100)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV BA folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 100 CV BA TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(100):
        loc = "Hà Nội" if j < 50 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        
        # Choose role type
        role_type = random.choice(["Business Analyst", "Technical Business Analyst", "Product Analyst", "Agile Business Analyst"])
        
        configs.append({
            "specialty": "Business Analyst",
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
            if "Business Analyst" in pos:
                # e.g., "Senior Business Analyst" -> "Senior Technical Business Analyst"
                exp["position"] = pos.replace("Business Analyst", role_type)
            elif "Developer" in pos:
                exp["position"] = pos.replace("Developer", role_type)
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "ba"
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

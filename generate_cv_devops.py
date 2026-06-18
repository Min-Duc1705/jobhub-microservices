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

# Dynamically inject DevOps data pools into generate_pdf_resumes
generate_pdf_resumes.SPECIALTIES["DevOps"] = {
    "title": "DevOps Engineer",
    "skills": [
        {"category": "Cloud & Infrastructure", "items": ["Amazon Web Services (AWS)", "Microsoft Azure", "Google Cloud Platform (GCP)", "Infrastructure as Code (IaC) - Terraform"]},
        {"category": "Container & Orchestration", "items": ["Docker & Containers", "Kubernetes (K8s)", "Helm Charts", "Service Mesh (Istio)"]},
        {"category": "CI/CD & Automation", "items": ["Jenkins / GitLab CI", "GitHub Actions", "Ansible / Chef", "Scripting (Bash, Python)"]}
    ],
    "projects": [
        {"name": "Cloud Infrastructure Modernization", "description": "Thiết kế và triển khai hạ tầng đám mây tự động hóa hoàn toàn sử dụng Terraform trên AWS. Container hóa các microservices bằng Docker và triển khai Kubernetes cluster (EKS), giảm 40% chi phí vận hành hạ tầng.", "tags": ["AWS", "Kubernetes", "Terraform", "Docker"]},
        {"name": "Automated CI/CD Deployment Pipeline", "description": "Xây dựng quy trình tích hợp và triển khai liên tục (CI/CD) tự động từ mã nguồn đến môi trường production sử dụng GitLab CI và GitOps (ArgoCD). Rút ngắn thời gian release từ 2 ngày xuống còn 10 phút.", "tags": ["GitLab CI", "ArgoCD", "Kubernetes", "Helm"]}
    ],
    "experiences": [
        {"position": "DevOps Engineer", "bullets": [
            "Quản lý và vận hành hệ thống máy chủ Linux, hỗ trợ cài đặt môi trường cho các nhóm phát triển.",
            "Xây dựng các pipeline tích hợp liên tục (CI) cơ bản bằng GitHub Actions và Jenkins.",
            "Viết các script Bash và Python để tự động hóa các tác vụ sao lưu dữ liệu và giám sát hệ thống."
        ]},
        {"position": "Senior DevOps Engineer", "bullets": [
            "Thiết kế kiến trúc hệ thống Kubernetes chịu tải cao và cấu hình auto-scaling phục vụ hàng triệu người dùng.",
            "Triển khai chiến lược quản lý cấu hình hạ tầng dạng mã (IaC) sử dụng Terraform và Ansible.",
            "Thiết lập hệ thống giám sát và cảnh báo tập trung sử dụng Prometheus, Grafana và ELK Stack, nâng cao độ tin cậy hệ thống lên 99.99%."
        ]}
    ]
}

generate_pdf_resumes.SUMMARIES["DevOps"] = [
    "Kỹ sư DevOps giàu kinh nghiệm với hơn 5 năm thực chiến thiết kế hạ tầng đám mây (AWS/Azure) và vận hành hệ thống Kubernetes. Am hiểu sâu sắc về Infrastructure as Code (Terraform), thiết lập CI/CD GitOps pipelines và tối ưu hóa hệ thống chịu tải cao. Đam mê tự động hóa và thúc đẩy văn hóa phối hợp Dev-Ops.",
    "Kỹ sư DevOps năng động có nền tảng tốt về hệ thống Linux và hạ tầng mạng. Có kinh nghiệm làm việc với Docker, CI/CD pipelines và các công cụ giám sát Prometheus/Grafana. Luôn sẵn sàng nghiên cứu các giải pháp tự động hóa mới để nâng cao hiệu quả vận hành."
]

generate_pdf_resumes.CERTIFICATES_POOL["DevOps"] = [
    {"date": "08/2025", "title": "Certified Kubernetes Administrator (CKA)"},
    {"date": "02/2025", "title": "AWS Certified DevOps Engineer - Professional"},
    {"date": "04/2026", "title": "TOEIC 845 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
]

generate_pdf_resumes.REFERENCES_POOL["DevOps"] = [
    "Phạm Minh Tuấn - DevOps Tech Lead tại VNG Corporation - SĐT: 0912345678 - Email: tuanpm@vng.com.vn",
    "Nguyễn Hoàng Nam - Infrastructure Manager tại FPT Software - Email: namnh@fsoft.com.vn"
]

def build_unique_names(count=100):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++", "CV ReactJS", "CV Angular", "CV VueJS", "CV fullstack", "CV devops"]:
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
                
    # 3. Shuffle with seed 2070 (fresh diversity and uniqueness)
    random.seed(2070)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV devops")
    
    # Get unique names first
    unique_names = build_unique_names(100)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV devops folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 100 CV DEVOPS TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(100):
        loc = "Hà Nội" if j < 50 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        configs.append({
            "specialty": "DevOps",
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
        profile["specialty"] = "DevOps Engineer"
        profile["title"] = "DevOps Engineer"
        
        # Adjust experiences' position titles to match
        for exp in profile["experiences"]:
            pos = exp["position"]
            if "DevOps Engineer" in pos:
                pass
            elif "Developer" in pos:
                exp["position"] = pos.replace("Developer", "DevOps Engineer")
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "devops"
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

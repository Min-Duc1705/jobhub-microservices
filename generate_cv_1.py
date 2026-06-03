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
    from generate_pdf_resumes import (
        generate_candidate_profile,
        generate_pdf_cv,
        generate_pdf_cv_two_column,
        generate_pdf_cv_template_3,
        generate_pdf_cv_template_4,
        generate_pdf_cv_template_5,
        ADDRESSES,
        SPECIALTIES,
        FIRST_NAMES,
        MIDDLE_NAMES,
        LAST_NAMES,
        make_slug
    )
except ImportError as e:
    print(f"[Error] Failed to import from generate_pdf_resumes.py: {e}")
    sys.exit(1)

def build_unique_names(count=100):
    names = []
    for f in FIRST_NAMES:
        for m in MIDDLE_NAMES:
            for l in LAST_NAMES:
                names.append((f, m, l))
    random.seed(42)  # For reproducibility
    random.shuffle(names)
    return [f"{n[0]} {n[1]} {n[2]}" for n in names[:count]]

def main():
    output_dir = "CV-1"
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV-1 folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 100 CV ĐA DẠNG TRONG THƯ MỤC: {output_dir} ===")
    print(f"Số lượng địa chỉ trong danh sách: {len(ADDRESSES)}")
    
    unique_names = build_unique_names(100)
    # Only include Frontend, Backend, DevOps, and QA Automation roles
    specialties_list = [
        s for s in SPECIALTIES.keys()
        if "Frontend" in s or "Backend" in s or s in ["DevOps", "QA Automation"]
    ]
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    success = 0
    for i in range(100):
        # 1. Unique Name
        full_name = unique_names[i]
        
        # 2. Specialty (Frontend, Backend, DevOps, Tester, Mobile, AI)
        specialty = specialties_list[i % len(specialties_list)]
        
        # 3. Level
        level = levels[i % len(levels)]
        
        # 4. Experience Years based on level
        exp_years = 0
        if level == "FRESHER": exp_years = random.choice([0, 1])
        elif level == "JUNIOR": exp_years = random.randint(1, 2)
        elif level == "MIDDLE": exp_years = random.randint(3, 4)
        elif level == "SENIOR": exp_years = random.randint(5, 7)
        elif level == "LEADER": exp_years = random.randint(7, 9)
        elif level == "MANAGER": exp_years = random.randint(9, 12)
        
        # 5. Address (sequentially ensuring each of 35 is used at least once)
        loc = ADDRESSES[i % len(ADDRESSES)]
        
        # 6. Template (cycling templates 1 to 5)
        curr_template = (i % 5) + 1
        
        # 7. Generate Candidate Profile
        profile = generate_candidate_profile(full_name, specialty, level, exp_years, location=loc)
        
        # 8. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = specialty.lower().replace(" .", "").replace(" & ", "_").replace(" ", "_")
        file_name = f"cv_{name_slug}_{spec_slug}_{level.lower()}.pdf"
        file_path = os.path.join(output_dir, file_name)
        
        # 9. Generate PDF based on template choice
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
                
            success += 1
            print(f"[{success}/100] Đã tạo Mẫu {curr_template} | {loc} | {specialty} | Level: {level} -> {file_name}")
        except Exception as e:
            print(f"❌ Lỗi khi tạo file {file_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ HOÀN THÀNH! Đã tạo thành công {success}/100 CV trong thư mục {output_dir}")

if __name__ == "__main__":
    main()

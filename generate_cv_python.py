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
        generate_pdf_cv_template_6,
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

def build_unique_names(count=50):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python"]:
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
                
    # 3. Shuffle with seed 2029 (fresh diversity and uniqueness)
    random.seed(2029)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV Python")
    
    # Get unique names first
    unique_names = build_unique_names(50)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV Python folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 50 CV BACKEND PYTHON (FASTAPI, DJANGO) TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(50):
        loc = "Hà Nội" if j < 25 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        configs.append({
            "specialty": "Backend Python",
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
        
        # Customizing profile to explicitly highlight FastAPI & Django in title/specialty
        profile["specialty"] = "Backend Python (FastAPI, Django)"
        profile["title"] = "Python Developer (FastAPI, Django)"
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "backend_python"
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
            print(f"[{success}/50] Đã tạo Mẫu {curr_template} | {loc} | {specialty} | Level: {level} -> {file_name}")
        except Exception as e:
            print(f"❌ Lỗi khi tạo file {file_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ HOÀN THÀNH! Đã tạo thành công {success}/50 CV trong thư mục {output_dir}")

if __name__ == "__main__":
    main()

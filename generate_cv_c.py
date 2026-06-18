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

# Dynamically inject C/C++ data pools into generate_pdf_resumes
generate_pdf_resumes.SPECIALTIES["Backend C"] = {
    "title": "C/C++ Engineer",
    "skills": [
        {"category": "Ngôn ngữ & Cốt lõi", "items": ["C/C++ (C++11/14/17/20)", "STL & Template Programming", "Memory Management & Pointers", "Data Structures & Algorithms"]},
        {"category": "Nhúng & Hệ thống", "items": ["Embedded Systems (ARM Cortex, ESP32)", "Real-Time OS (FreeRTOS, VxWorks)", "Linux System Programming & Multi-threading", "Linux Kernel & Device Drivers"]},
        {"category": "Công cụ & Giao thức", "items": ["GDB, Valgrind, CMake", "UART, SPI, I2C, CAN Bus", "Docker & Git", "Socket Programming (TCP/IP)"]}
    ],
    "projects": [
        {"name": "Embedded Smart Gateway", "description": "Thiết kế và lập trình phần mềm nhúng cho thiết bị Gateway giám sát công nghiệp thông minh dựa trên MCU ARM Cortex-M4 và FreeRTOS. Tối ưu hóa bộ nhớ heap/stack và quản lý tài nguyên, tích hợp các giao thức truyền thông UART, SPI, Modbus RTU và truyền tải dữ liệu cảm biến thời gian thực, tiết kiệm năng lượng 30%.", "tags": ["C/C++", "FreeRTOS", "ARM Cortex", "Modbus", "SPI/I2C"]},
        {"name": "High-Performance Network Proxy", "description": "Phát triển ứng dụng proxy mạng hiệu năng cao bằng C++17 sử dụng mô hình lập trình bất đồng bộ Asynchronous I/O (epoll trên Linux). Thiết kế cơ chế Thread Pool và Object Pool tối ưu hóa cấp phát bộ nhớ, xử lý hơn 100,000 requests/giây với độ trễ cực thấp.", "tags": ["C++17", "Linux Systems", "Socket Programming", "Multi-threading"]},
        {"name": "Automotive CAN Bus Controller", "description": "Xây dựng trình điều khiển thiết bị (Device Driver) cho bộ điều khiển CAN Bus trong hệ thống nhúng ô tô (Automotive) tuân thủ tiêu chuẩn MISRA C. Tối ưu hóa xử lý ngắt (Interrupt Service Routine - ISR) đạt độ trễ phản hồi dưới 5 microseconds.", "tags": ["C", "Embedded Software", "CAN Bus", "MISRA C", "Device Drivers"]}
    ],
    "experiences": [
        {"position": "C/C++ Developer", "bullets": [
            "Phát triển và bảo trì mã nguồn C/C++ cho các ứng dụng hệ thống và firmware nhúng.",
            "Lập trình tương tác với phần cứng qua các giao thức SPI, I2C, UART trên các vi điều khiển STM32/ESP32.",
            "Sử dụng các công cụ debugger GDB, J-Link để dò lỗi phần cứng và rò rỉ bộ nhớ (memory leaks) bằng Valgrind.",
            "Thực hiện viết unit test sử dụng Google Test để đảm bảo chất lượng của các module phần mềm nhúng."
        ]},
        {"position": "Senior C/C++ Engineer", "bullets": [
            "Thiết kế kiến trúc hệ thống nhúng thời gian thực và lựa chọn hệ điều hành RTOS phù hợp với yêu cầu phần cứng.",
            "Tối ưu hóa mã nguồn C/C++ ở mức độ biên dịch, tối ưu cấu trúc dữ liệu và giải thuật giúp giảm 40% dung lượng bộ nhớ RAM/Flash sử dụng.",
            "Xây dựng các driver hệ thống và module nhân Linux (Linux Kernel Modules) cho các thiết bị ngoại vi đặc thù.",
            "Hướng dẫn các kỹ sư junior tuân thủ các quy tắc lập trình an toàn MISRA C/C++ và review code hàng tuần."
        ]}
    ]
}

generate_pdf_resumes.SUMMARIES["Backend C"] = [
    "Kỹ sư hệ thống C/C++ giàu kinh nghiệm chuyên sâu về lập trình hệ thống Linux và thiết kế firmware nhúng. Am hiểu sâu sắc về quản lý bộ nhớ thủ công, lập trình đa luồng (multi-threading) và tối ưu hóa hiệu năng phần cứng. Luôn hướng tới viết code an toàn, hiệu năng cao và tuân thủ các tiêu chuẩn công nghiệp.",
    "Lập trình viên C/C++ nhúng và hệ thống có nền tảng toán học và thuật toán vững chắc. Có kinh nghiệm thực chiến phát triển trên các hệ điều hành thời gian thực (RTOS) và thiết bị vi điều khiển ARM. Sẵn sàng học hỏi công nghệ mới và giải quyết các bài toán tối ưu hóa tài nguyên phần cứng."
]

generate_pdf_resumes.CERTIFICATES_POOL["Backend C"] = [
    {"date": "08/2025", "title": "Advanced C++ Certified Professional - C++ Institute"},
    {"date": "02/2025", "title": "Embedded Systems Engineering Certificate - Coursera / UC Boulder"},
    {"date": "04/2026", "title": "TOEIC 850 - Chứng chỉ tiếng Anh giao tiếp quốc tế"}
]

generate_pdf_resumes.REFERENCES_POOL["Backend C"] = [
    "Trần Văn Cường - Solution Architect tại FPT Software - SĐT: 0912345678 - Email: cuongtv@fsoft.com.vn",
    "Nguyễn Minh Đức - Technical Director tại Viettel High Technology - Email: ducnm@viettel.com.vn"
]

def build_unique_names(count=50):
    # 1. Gather all name slugs from existing CV directories to exclude them
    existing_slugs = set()
    for folder in ["CV", "CV-1", "CV NET", "CV java", "CV Python", "CV NodeJS", "CV PHP", "CV C_C++"]:
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
                
    # 3. Shuffle with seed 2035 (fresh diversity and uniqueness)
    random.seed(2035)
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
    output_dir = os.path.join("T:\\TryHard_IT_Project\\Final\\Backend", "CV C_C++")
    
    # Get unique names first
    unique_names = build_unique_names(50)
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"[Warning] Failed to delete existing CV C_C++ folder: {e}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU SINH 50 CV C/C++ TRONG THƯ MỤC: {output_dir} ===")
    
    levels = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    
    configs = []
    for j in range(50):
        loc = "Hà Nội" if j < 25 else "TP. Hồ Chí Minh"
        level = levels[j % len(levels)]
        # Use all 6 templates evenly
        curr_template = (j % 6) + 1
        
        # Randomly choose one of the three C/C++ roles
        role_type = random.choice(["System Engineer", "Embedded Software Engineer", "Developer"])
        
        configs.append({
            "specialty": "Backend C",
            "location": loc,
            "level": level,
            "template": curr_template,
            "role_type": role_type
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
        profile["specialty"] = f"C/C++ ({role_type})"
        profile["title"] = f"C/C++ {role_type}"
        
        # Adjust experiences' position titles to match
        for exp in profile["experiences"]:
            pos = exp["position"]
            if "C/C++ Engineer" in pos:
                exp["position"] = pos.replace("C/C++ Engineer", role_type)
            elif "C/C++ Developer" in pos:
                exp["position"] = pos.replace("C/C++ Developer", role_type)
        
        # 5. Define Output Path
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = "backend_c"
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

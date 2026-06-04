import psycopg2
import sys

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "root",
    "dbname": "JobService"
}

# The 5 real IT jobs from job.vccorp.vn with raw VND salaries
REAL_VCCORP_JOBS = [
    {
        "name": "Lập trình viên Web .NET",
        "level": "MIDDLE",
        "salary_min": 15000000.0,
        "salary_max": 30000000.0,
        "currency": "VND",
        "desc": "Phát triển các hệ thống Web và API nghiệp vụ cho các khối sản phẩm của VCCorp (Admicro, Bizfly). Tham gia tối ưu hóa hiệu năng ứng dụng, bảo trì hệ thống chạy trên nền C# / .NET.",
        "req": "Có từ 2 năm kinh nghiệm làm việc với C# và ASP.NET MVC / Web API. Hiểu biết tốt về cơ sở dữ liệu SQL Server hoặc PostgreSQL. Có tư duy logic tốt và kỹ năng làm việc nhóm.",
        "benefits": "Lương cứng cạnh tranh từ 15.000.000 - 30.000.000 VNĐ + thưởng hiệu quả công việc. Chế độ bảo hiểm đầy đủ, teambuilding, review lương hàng năm.",
        "skills": ["c#", ".net", "microsoft sql server", "rest api", "git"]
    },
    {
        "name": "Lập trình viên Fullstack (ReactJs, .NET Core)",
        "level": "MIDDLE",
        "salary_min": 25000000.0,
        "salary_max": 35000000.0,
        "currency": "VND",
        "desc": "Tham gia thiết kế và phát triển các sản phẩm công nghệ chuyển đổi số (Bizfly) từ giao diện frontend (ReactJS, TypeScript) đến hệ thống dịch vụ backend (.NET Core).",
        "req": "Tối thiểu 3 năm kinh nghiệm lập trình. Thành thạo lập trình frontend ReactJS, HTML5, CSS3, TypeScript và backend C# / .NET Core. Có kinh nghiệm làm việc với RESTful API và Docker.",
        "benefits": "Mức lương cứng từ 25.000.000 - 35.000.000 VNĐ. Gói chăm sóc sức khỏe toàn diện. Môi trường làm việc chuyên nghiệp, nhiều cơ hội thăng tiến lên Tech Lead.",
        "skills": ["react", "typescript", "c#", ".net", "javascript"]
    },
    {
        "name": "Kỹ sư kiểm thử phần mềm (QA QC Tester)",
        "level": "JUNIOR",
        "salary_min": 10000000.0,
        "salary_max": 20000000.0,
        "currency": "VND",
        "desc": "Thực hiện kiểm thử chất lượng các phần mềm, website, app di động của VCCorp. Lập test case, chuẩn bị data test, thực hiện kiểm thử và ghi nhận lỗi lên hệ thống quản lý lỗi (Jira).",
        "req": "Có ít nhất 1-2 năm kinh nghiệm kiểm thử phần mềm (Manual Test). Hiểu rõ quy trình phát triển và kiểm thử phần mềm (Agile/Scrum). Ưu tiên ứng viên có kiến thức cơ bản về Automation Test.",
        "benefits": "Mức lương cứng từ 10.000.000 - 20.000.000 VNĐ. Thử việc hưởng full lương. Gói khám sức khỏe định kỳ hàng năm.",
        "skills": ["testing", "qa qc", "git", "agile"]
    },
    {
        "name": "Lập trình viên NodeJS (Backend Engineer)",
        "level": "JUNIOR",
        "salary_min": 10000000.0,
        "salary_max": 20000000.0,
        "currency": "VND",
        "desc": "Phát triển các dịch vụ API backend chịu tải cao sử dụng Node.js (Express, NestJS) phục vụ các hệ thống đọc báo và dịch vụ nội dung số của VCCorp.",
        "req": "Yêu cầu từ 1-2 năm kinh nghiệm phát triển Backend Node.js. Am hiểu cơ sở dữ liệu MongoDB hoặc PostgreSQL. Có kinh nghiệm với Redis, Socket.io là một lợi thế.",
        "benefits": "Mức lương cứng từ 10.000.000 - 20.000.000 VNĐ. Cung cấp trang thiết bị làm việc hiện đại. Hỗ trợ tiền ăn trưa và gửi xe.",
        "skills": ["node.js", "express.js", "nestjs", "mongodb", "git"]
    },
    {
        "name": "Chuyên viên phân tích nghiệp vụ (Business Analyst)",
        "level": "MIDDLE",
        "salary_min": 23000000.0,
        "salary_max": 40000000.0,
        "currency": "VND",
        "desc": "Khảo sát và thu thập yêu cầu từ khách hàng và các bộ phận nghiệp vụ thuộc khối Admicro/Bizfly. Phân tích yêu cầu và viết tài liệu mô tả yêu cầu nghiệp vụ (SRS), vẽ sơ đồ luồng (Workflow) để chuyển giao cho đội phát triển.",
        "req": "Có ít nhất 2 năm kinh nghiệm làm BA phần mềm. Khả năng phân tích logic và viết tài liệu tốt. Sử dụng thành thạo các công cụ vẽ luồng (Figma, Visio, Draw.io) và có kỹ năng giao tiếp tốt.",
        "benefits": "Mức lương cứng từ 23.000.000 - 40.000.000 VNĐ. Lương tháng 13 + thưởng KPIs dự án hấp dẫn. Review tăng lương hàng năm.",
        "skills": ["agile", "sql", "jira", "git"]
    }
]

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== BẮT ĐẦU CẬP NHẬT JOBS VCCORP THÀNH TIỀN VNĐ ===")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"], 
            port=DB_CONFIG["port"], 
            dbname=DB_CONFIG["dbname"], 
            user=DB_CONFIG["user"], 
            password=DB_CONFIG["password"]
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Không thể kết nối CSDL: {e}")
        return

    # 1. Fetch current jobs for VCCorp
    cur.execute('SELECT "Id" FROM "Jobs" WHERE "CompanyName" = \'VCCorp\' ORDER BY "Id"')
    job_ids = [row[0] for row in cur.fetchall()]
    
    print(f"Tìm thấy {len(job_ids)} jobs của VCCorp trong CSDL.")
        
    # 2. Get skills map
    cur.execute('SELECT "Id", "Name" FROM "Skills"')
    skills_data = cur.fetchall()
    skill_map = {row[1].lower().strip(): row[0] for row in skills_data}
    
    # 3. Update VCCorp jobs in database
    updated_count = 0
    for idx, job_id in enumerate(job_ids):
        if idx >= len(REAL_VCCORP_JOBS):
            break
            
        real_job = REAL_VCCORP_JOBS[idx]
        print(f"Đang cập nhật Job {idx+1}: {real_job['name']} (VNĐ)...")
        
        # Update Job fields
        cur.execute('''
            UPDATE "Jobs"
            SET "Name" = %s, "Level" = %s, "SalaryMin" = %s, "SalaryMax" = %s, "SalaryCurrency" = %s,
                "Description" = %s, "Requirements" = %s, "Benefits" = %s, "Category" = 'SOFTWARE_SERVICES'
            WHERE "Id" = %s
        ''', (
            real_job["name"], real_job["level"], real_job["salary_min"], real_job["salary_max"], real_job["currency"],
            real_job["desc"], real_job["req"], real_job["benefits"], job_id
        ))
        
        # Clear old JobSkills
        cur.execute('DELETE FROM "JobSkills" WHERE "JobId" = %s', (job_id,))
        
        # Insert new JobSkills
        for skill_tag in real_job["skills"]:
            skill_id = None
            clean_tag = skill_tag.lower().strip()
            
            aliases = {
                'react': 'react',
                'typescript': 'typescript',
                'c#': 'c#',
                '.net': 'c#',
                'javascript': 'javascript',
                'testing': 'testing',
                'qa qc': 'testing',
                'git': 'git',
                'agile': 'agile',
                'node.js': 'node.js',
                'express.js': 'express.js',
                'nestjs': 'nestjs',
                'mongodb': 'mongodb',
                'sql': 'microsoft sql server',
                'jira': 'agile'
            }
            if clean_tag in aliases:
                clean_tag = aliases[clean_tag]
                
            if clean_tag in skill_map:
                skill_id = skill_map[clean_tag]
                
            if skill_id:
                cur.execute('INSERT INTO "JobSkills" ("JobId", "SkillId") VALUES (%s, %s) ON CONFLICT DO NOTHING', (job_id, skill_id))
                
        updated_count += 1
        
    conn.commit()
    print(f"\n=== HOÀN THÀNH CẬP NHẬT VNĐ ===")
    print(f"Đã cập nhật thành công {updated_count} jobs của VCCorp thành đơn vị tiền tệ VNĐ chuẩn!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

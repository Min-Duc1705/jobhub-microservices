import sys
import random
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "root",
    "dbname": "JobService"
}

def calculate_realistic_salary(level, category, title):
    # Base salary ranges in USD for IT market in Vietnam in 2026
    base_ranges = {
        "INTERN": (250, 450),
        "FRESHER": (500, 850),
        "JUNIOR": (900, 1400),
        "MIDDLE": (1600, 2600),
        "SENIOR": (2800, 4600),
        "LEADER": (4200, 6200),
        "MANAGER": (5200, 8500)
    }
    
    s_min, s_max = base_ranges.get(level, (1500, 2500))
    
    # Premium multipliers for high-demand domains/tech stacks
    multiplier = 1.0
    title_lower = title.lower()
    
    # AI/ML gets the highest premium (25-30%)
    if category == 'AI_ML' or any(k in title_lower for k in ['ai', 'learning', 'vision', 'nlp', 'data scientist']):
        multiplier = 1.28
    # Fintech/Banking and Cybersecurity get a 15% premium
    elif category in ['FINTECH_BANKING', 'CYBERSECURITY'] or 'security' in title_lower or 'banking' in title_lower:
        multiplier = 1.15
    # Telecom/Networking and Game get an 8% premium
    elif category in ['TELECOM_NETWORKING', 'GAME']:
        multiplier = 1.08
        
    s_min = int(s_min * multiplier)
    s_max = int(s_max * multiplier)
    
    # Add slight realistic variance (+/- 8%) representing candidate negotiation / company budget variance
    fluctuation_min = random.uniform(-0.08, 0.08)
    fluctuation_max = random.uniform(-0.08, 0.08)
    
    final_min = int(s_min * (1 + fluctuation_min))
    final_max = int(s_max * (1 + fluctuation_max))
    
    # Ensure min salary is bound and max is strictly greater than min
    final_min = max(200, final_min)
    if final_max <= final_min:
        final_max = final_min + random.randint(300, 800)
        
    # Round to nearest 50 USD for professional look
    final_min = round(final_min / 50) * 50
    final_max = round(final_max / 50) * 50
    
    return final_min, final_max

def main():
    print("=== ĐANG BẮT ĐẦU CẬP NHẬT LƯƠNG CHUẨN ĐỂ HUẤN LUYỆN AI ===")
    
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

    # Load all jobs with necessary features
    cur.execute('SELECT "Id", "Level", "Category", "Name" FROM "Jobs"')
    jobs = cur.fetchall()
    print(f"Tìm thấy {len(jobs)} jobs trong database để cập nhật lương.")
    
    updated_count = 0
    for job_id, level, category, title in jobs:
        # Calculate standard salary range based on level, domain, and title
        salary_min, salary_max = calculate_realistic_salary(level, category, title)
        
        # Update salary in DB
        cur.execute('''
            UPDATE "Jobs"
            SET "SalaryMin" = %s, "SalaryMax" = %s, "SalaryCurrency" = 'USD', "IsSalaryNegotiable" = %s
            WHERE "Id" = %s
        ''', (float(salary_min), float(salary_max), random.choice([True, False, False]), job_id))
        
        updated_count += 1
        if updated_count % 100 == 0:
            print(f"  -> Đã cập nhật xong lương cho {updated_count}/1000 jobs.")
            
    conn.commit()
    print(f"\n=== HOÀN THÀNH CẬP NHẬT LƯƠNG CHUẨN ===")
    print(f"Đã cập nhật thành công {updated_count} jobs với mức lương thực tế chuẩn theo thị trường năm 2026!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

import psycopg2

def inspect():
    cand_ids = ('ea692780-f0f7-493c-baac-7a886a32209f', '134a753f-2779-4a09-b9b9-17f72205938d')
    job_id = '90229569-027b-4328-aef7-2b41e710ef3b'
    
    try:
        # 1. Connect to ProfileService
        conn_p = psycopg2.connect(host='localhost', port=5432, dbname='ProfileService', user='postgres', password='root')
        cur_p = conn_p.cursor()
        cur_p.execute('SELECT "Id", "FullName", "IsDeleted" FROM "Customers" WHERE "Id" IN %s', (cand_ids,))
        print("=== PROFILE SERVICE: CUSTOMERS ===")
        for row in cur_p.fetchall():
            print(row)
        conn_p.close()
        
        # 2. Connect to ResumeService - Resumes
        conn_r = psycopg2.connect(host='localhost', port=5432, dbname='ResumeService', user='postgres', password='root')
        cur_r = conn_r.cursor()
        cur_r.execute('SELECT "Id", "CustomerId", "Title", "IsDeleted" FROM "Resumes" WHERE "CustomerId" IN %s', (cand_ids,))
        print("\n=== RESUME SERVICE: RESUMES ===")
        for row in cur_r.fetchall():
            print(row)
            
        # 3. Connect to ResumeService - Applications
        cur_r.execute('SELECT "Id", "CustomerId", "JobId", "ResumeId", "IsDeleted" FROM "Applications" WHERE "JobId" = %s', (job_id,))
        print(f"\n=== RESUME SERVICE: APPLICATIONS FOR JOB {job_id} ===")
        for row in cur_r.fetchall():
            print(row)
            
        conn_r.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

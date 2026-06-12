import psycopg2

def inspect():
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='ResumeService', user='postgres', password='root')
        cur = conn.cursor()
        
        # List tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print("=== TABLES IN RESUMESERVICE ===")
        for row in cur.fetchall():
            print(f"  {row[0]}")
            
        # Inspect columns of Applications
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'Applications'
        """)
        print("\n=== COLUMNS IN Applications ===")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
            
        # Select all applications
        cur.execute('SELECT * FROM "Applications"')
        print("\n=== ALL APPLICATIONS ===")
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        for row in rows:
            print(dict(zip(colnames, row)))
            
        # Select applications for the specific Job ID
        job_id = '90229569-027b-4328-aef7-2b41e710ef3b'
        cur.execute('SELECT * FROM "Applications" WHERE "JobId" = %s', (job_id,))
        print(f"\n=== APPLICATIONS FOR JOB {job_id} ===")
        rows = cur.fetchall()
        for row in rows:
            print(dict(zip(colnames, row)))
            
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

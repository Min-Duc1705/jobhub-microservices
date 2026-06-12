import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="ResumeService",
    user="postgres",
    password="root"
)
cur = conn.cursor()

# Get applications for specific job
cur.execute('SELECT "Id", "CustomerId", "ResumeId", "Status", "IsDeleted" FROM "Applications" WHERE "JobId" = \'90229569-027b-4328-aef7-2b41e710ef3b\';')
apps = cur.fetchall()

print("Checking resumes for job 90229569-027b-4328-aef7-2b41e710ef3b:")
for app in apps:
    app_id, cust_id, resume_id, status, is_deleted = app
    cur.execute('SELECT "Id", "Title", "IsDeleted" FROM "Resumes" WHERE "Id" = %s;', (resume_id,))
    resume = cur.fetchone()
    print(f"AppId: {app_id} | CustId: {cust_id} | ResumeId: {resume_id} | AppIsDeleted: {is_deleted}")
    if resume:
        print(f"  -> Found Resume: Title='{resume[1]}', IsDeleted={resume[2]}")
    else:
        print(f"  -> ❌ Resume NOT FOUND in DB!")

cur.close()
conn.close()

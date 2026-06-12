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
cur.execute('SELECT "Id", "CustomerId", "JobId", "Status", "CreatedDate" FROM "Applications" WHERE "JobId" = \'90229569-027b-4328-aef7-2b41e710ef3b\';')
rows = cur.fetchall()
print("Applications for Job 90229569-027b-4328-aef7-2b41e710ef3b:")
for row in rows:
    print(f"AppId: {row[0]}, CustId: {row[1]}, Status: {row[3]}, CreatedDate: {row[4]}")

cur.close()
conn.close()

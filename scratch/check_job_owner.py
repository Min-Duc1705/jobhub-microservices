import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="JobService",
    user="postgres",
    password="root"
)
cur = conn.cursor()
cur.execute('SELECT "Id", "CustomerId", "Name", "CompanyName" FROM "Jobs" WHERE "Id" = \'90229569-027b-4328-aef7-2b41e710ef3b\';')
row = cur.fetchone()
print("Job Details:", row)
cur.close()
conn.close()

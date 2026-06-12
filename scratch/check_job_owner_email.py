import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="AuthService",
    user="postgres",
    password="root"
)
cur = conn.cursor()
cur.execute('SELECT "Email", "Username", "RoleId" FROM "AppUsers" WHERE "Id" = \'0739d6f3-f96e-4f4e-b4df-3c8261be467c\';')
row = cur.fetchone()
print("AppUser in Auth:", row)

conn_p = psycopg2.connect(
    host="localhost",
    port=5432,
    database="ProfileService",
    user="postgres",
    password="root"
)
cur_p = conn_p.cursor()
cur_p.execute('SELECT \"Id\", \"AppUserId\", \"FullName\" FROM \"Customers\" WHERE \"Id\" = \'0739d6f3-f96e-4f4e-b4df-3c8261be467c\' OR \"AppUserId\" = \'0739d6f3-f96e-4f4e-b4df-3c8261be467c\';')
row_p = cur_p.fetchall()
print("Customer in Profile:", row_p)

# If AppUserId found in Profile, fetch that user from Auth
if row_p:
    app_user_id = row_p[0][1]
    cur.execute('SELECT \"Email\", \"Username\" FROM \"AppUsers\" WHERE \"Id\" = %s;', (app_user_id,))
    row_user = cur.fetchone()
    print("Owner Auth User:", row_user)

cur.close()
conn.close()
cur_p.close()
conn_p.close()

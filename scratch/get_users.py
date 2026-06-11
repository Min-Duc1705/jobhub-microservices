import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

def main():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="AuthService",
            user="postgres",
            password="root"
        )
        cur = conn.cursor()
        
        # Get roles
        cur.execute('SELECT "Id", "Name" FROM "Roles"')
        roles = cur.fetchall()
        role_map = {r[0]: r[1] for r in roles}
        print("Roles in DB:", role_map)
        
        # Select some candidates
        candidate_role_id = [rid for rid, rname in role_map.items() if rname.upper() == 'CANDIDATE']
        if candidate_role_id:
            cur.execute('SELECT "Email", "Username" FROM "AppUsers" WHERE "RoleId" = %s LIMIT 5', (candidate_role_id[0],))
            print("\nCandidates:")
            for email, uname in cur.fetchall():
                print(f"Email: {email} | Username: {uname}")
                
        # Select some HRs
        hr_role_id = [rid for rid, rname in role_map.items() if rname.upper() == 'HR']
        if hr_role_id:
            cur.execute('SELECT "Email", "Username" FROM "AppUsers" WHERE "RoleId" = %s LIMIT 5', (hr_role_id[0],))
            print("\nHR Users:")
            for email, uname in cur.fetchall():
                print(f"Email: {email} | Username: {uname}")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

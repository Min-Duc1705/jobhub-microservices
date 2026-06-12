import psycopg2
import datetime

def inspect():
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='NotificationService', user='postgres', password='root')
        cur = conn.cursor()
        
        # Select messages after 2026-06-11 08:30:00 UTC
        utc_cutoff = datetime.datetime(2026, 6, 11, 8, 30, 0, tzinfo=datetime.timezone.utc)
        cur.execute('SELECT "Id", "SenderId", "Content", "Type", "CreatedAt" FROM "Messages" WHERE "CreatedAt" >= %s ORDER BY "CreatedAt" ASC', (utc_cutoff,))
        print("=== MESSAGES AFTER 08:30 UTC ===")
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        for row in rows:
            print(dict(zip(colnames, row)))
            
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

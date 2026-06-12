import psycopg2

def inspect():
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='NotificationService', user='postgres', password='root')
        cur = conn.cursor()
        
        # Select recent messages
        cur.execute('SELECT "Id", "SenderId", "Content", "Type", "CreatedAt" FROM "Messages" ORDER BY "CreatedAt" DESC LIMIT 30')
        print("=== RECENT MESSAGES ===")
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        for row in rows:
            print(dict(zip(colnames, row)))
            
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

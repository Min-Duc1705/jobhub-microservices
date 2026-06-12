import psycopg2

def inspect():
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='ResumeService', user='postgres', password='root')
        cur = conn.cursor()
        
        # Select all resumes for our candidate IDs
        cand_ids = ('ea692780-f0f7-493c-baac-7a886a32209f', '134a753f-2779-4a09-b9b9-17f72205938d')
        cur.execute('SELECT * FROM "Resumes" WHERE "CustomerId" IN %s', (cand_ids,))
        print("=== RESUMES FOR CANDIDATES ===")
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        for row in rows:
            print(dict(zip(colnames, row)))
            
        # Select candidates from ProfileService (if it exists in another database)
        conn2 = psycopg2.connect(host='localhost', port=5432, dbname='ProfileService', user='postgres', password='root')
        cur2 = conn2.cursor()
        cur2.execute('SELECT * FROM "Customers" WHERE "Id" IN %s', (cand_ids,))
        print("\n=== CUSTOMERS IN PROFILESERVICE ===")
        colnames2 = [desc[0] for desc in cur2.description]
        rows2 = cur2.fetchall()
        for row in rows2:
            print(dict(zip(colnames2, row)))
            
        conn.close()
        conn2.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

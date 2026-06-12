import psycopg2

def inspect():
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='ProfileService', user='postgres', password='root')
        cur = conn.cursor()
        
        # Print all Customers
        cur.execute('SELECT "Id", "FullName", "CompanyId", "IsDeleted" FROM "Customers"')
        print("\n=== ALL CUSTOMERS ===")
        for row in cur.fetchall():
            print(row)
            
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

import psycopg2

def inspect():
    try:
        conn_p = psycopg2.connect(host='localhost', port=5432, dbname='ProfileService', user='postgres', password='root')
        cur_p = conn_p.cursor()
        
        cur_p.execute('SELECT "Id", "FullName", "IsDeleted" FROM "Customers" WHERE "FullName" LIKE \'%Sơn%\' OR "FullName" LIKE \'%Hà%\'')
        print("=== PROFILE SERVICE: SEARCH BY NAME ===")
        for row in cur_p.fetchall():
            print(row)
            
        # Also, let's select all rows from Customers table to find how many customers exist
        cur_p.execute('SELECT COUNT(*) FROM "Customers"')
        print(f"Total customers: {cur_p.fetchone()[0]}")
        
        conn_p.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

import psycopg2

def inspect():
    cand_ids = ('ea692780-f0f7-493c-baac-7a886a32209f', '134a753f-2779-4a09-b9b9-17f72205938d')
    try:
        conn_p = psycopg2.connect(host='localhost', port=5432, dbname='ProfileService', user='postgres', password='root')
        cur_p = conn_p.cursor()
        
        cur_p.execute('SELECT * FROM "Customers" WHERE "AppUserId" IN %s', (cand_ids,))
        colnames = [desc[0] for desc in cur_p.description]
        print("=== PROFILE SERVICE: CUSTOMERS BY AppUserId ===")
        for row in cur_p.fetchall():
            print(dict(zip(colnames, row)))
            
        cur_p.execute('SELECT * FROM "Customers" WHERE "Id" IN %s', (cand_ids,))
        print("\n=== PROFILE SERVICE: CUSTOMERS BY Id ===")
        for row in cur_p.fetchall():
            print(dict(zip(colnames, row)))
            
        conn_p.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

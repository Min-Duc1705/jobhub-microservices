import psycopg2

def inspect():
    try:
        conn_p = psycopg2.connect(host='localhost', port=5432, dbname='ProfileService', user='postgres', password='root')
        cur_p = conn_p.cursor()
        
        cur_p.execute('SELECT * FROM "Customers" WHERE "FullName" IN (\'Bùi Phương Hà\', \'Lê Thị Sơn\')')
        colnames = [desc[0] for desc in cur_p.description]
        for row in cur_p.fetchall():
            print(dict(zip(colnames, row)))
            
        conn_p.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()

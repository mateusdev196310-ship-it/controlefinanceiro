import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        database='financeiro_db',
        user='postgres',
        password='masterkey'
    )
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cur.fetchall()
    print('Existing tables:')
    for table in tables:
        print(f'  - {table[0]}')
    conn.close()
except Exception as e:
    print(f'Error: {e}')
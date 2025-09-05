import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        database='financeiro_db',
        user='postgres',
        password='masterkey'
    )
    cur = conn.cursor()
    
    # Get all financas tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'financas_%';")
    tables = cur.fetchall()
    
    print('Dropping financas tables:')
    for table in tables:
        table_name = table[0]
        print(f'  - Dropping {table_name}')
        cur.execute(f'DROP TABLE IF EXISTS {table_name} CASCADE;')
    
    conn.commit()
    print('All financas tables dropped successfully!')
    conn.close()
except Exception as e:
    print(f'Error: {e}')
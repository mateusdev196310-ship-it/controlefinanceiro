import psycopg2

def reset_database():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='financeiro_db',
            user='postgres',
            password='masterkey'
        )
        cur = conn.cursor()
        
        # Listar todas as tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        all_tables = [table[0] for table in cur.fetchall()]
        
        # Tabelas do admin/Django que devem ser preservadas
        admin_tables = [
            'django_migrations',
            'django_content_type', 
            'auth_permission',
            'auth_group',
            'auth_group_permissions',
            'auth_user',
            'auth_user_groups', 
            'auth_user_user_permissions',
            'django_admin_log',
            'django_session'
        ]
        
        # Tabelas para dropar (todas exceto as do admin)
        tables_to_drop = [table for table in all_tables if table not in admin_tables]
        
        print(f"Tabelas encontradas: {len(all_tables)}")
        print(f"Tabelas do admin preservadas: {len(admin_tables)}")
        print(f"Tabelas a serem dropadas: {len(tables_to_drop)}")
        
        if tables_to_drop:
            print("\nDropando tabelas:")
            for table in tables_to_drop:
                print(f"  - Dropando {table}")
                cur.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
            
            conn.commit()
            print(f"\n✅ {len(tables_to_drop)} tabelas dropadas com sucesso!")
        else:
            print("\n✅ Nenhuma tabela para dropar (apenas tabelas do admin encontradas)")
        
        # Limpar dados dos usuários (manter apenas superuser se existir)
        print("\nLimpando dados de usuários de teste...")
        cur.execute("DELETE FROM auth_user WHERE is_superuser = false;")
        deleted_users = cur.rowcount
        
        conn.commit()
        print(f"✅ {deleted_users} usuários de teste removidos")
        
        # Verificar tabelas restantes
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        remaining_tables = [table[0] for table in cur.fetchall()]
        print(f"\nTabelas restantes: {len(remaining_tables)}")
        for table in remaining_tables:
            print(f"  - {table}")
        
        conn.close()
        print("\n🎉 Database resetado com sucesso! Pronto para teste do zero.")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    reset_database()
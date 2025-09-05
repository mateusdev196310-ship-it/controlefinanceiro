import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def create_database():
    try:
        # Conectar ao PostgreSQL (banco padrão 'postgres')
        connection = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='masterkey',
            database='postgres'  # Conectar ao banco padrão
        )
        
        # Configurar para autocommit
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Criar cursor
        cursor = connection.cursor()
        
        # Verificar se o banco já existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='financeiro_db'")
        exists = cursor.fetchone()
        
        if not exists:
            # Criar o banco de dados
            cursor.execute('CREATE DATABASE financeiro_db')
            print("Banco de dados 'financeiro_db' criado com sucesso!")
        else:
            print("Banco de dados 'financeiro_db' já existe.")
        
        # Fechar conexões
        cursor.close()
        connection.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"Erro ao criar banco de dados: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False

if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)
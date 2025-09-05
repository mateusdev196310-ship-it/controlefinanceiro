import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_customuser_table():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando campos faltantes na tabela auth_user_custom...")
        
        # Lista de campos para adicionar
        fields_to_add = [
            ('razao_social', 'VARCHAR(200) DEFAULT \'\''),
            ('nome_fantasia', 'VARCHAR(200) DEFAULT \'\''),
            ('endereco_logradouro', 'VARCHAR(200) DEFAULT \'\''),
            ('endereco_numero', 'VARCHAR(20) DEFAULT \'\''),
            ('endereco_complemento', 'VARCHAR(100) DEFAULT \'\''),
            ('endereco_bairro', 'VARCHAR(100) DEFAULT \'\''),
            ('endereco_municipio', 'VARCHAR(100) DEFAULT \'\''),
            ('endereco_uf', 'VARCHAR(2) DEFAULT \'\''),
            ('endereco_cep', 'VARCHAR(9) DEFAULT \'\''),
            ('telefone', 'VARCHAR(20) DEFAULT \'\''),
            ('celular', 'VARCHAR(20) DEFAULT \'\''),
            ('data_nascimento', 'DATE'),
            ('profissao', 'VARCHAR(100) DEFAULT \'\''),
            ('renda_mensal', 'DECIMAL(10, 2)'),
            ('observacoes', 'TEXT DEFAULT \'\''),
            ('ativo', 'BOOLEAN DEFAULT TRUE'),
            ('data_cadastro', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
            ('data_atualizacao', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
        ]
        
        for field_name, field_definition in fields_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE auth_user_custom 
                    ADD COLUMN IF NOT EXISTS {field_name} {field_definition};
                """)
                print(f"  ✅ Campo {field_name} adicionado")
            except Exception as e:
                print(f"  ⚠️ Campo {field_name}: {e}")
        
        # Verificar estrutura final da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'auth_user_custom'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Estrutura final da tabela auth_user_custom ({len(columns)} campos):")
        for column_name, data_type, nullable, default in columns:
            print(f"  - {column_name}: {data_type} (nullable: {nullable})")
        
        print("\n🎉 Tabela auth_user_custom atualizada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_customuser_table()
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def complete_customuser_table():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando todos os campos faltantes na tabela auth_user_custom...")
        
        # Lista completa de campos para adicionar
        additional_fields = [
            ('celular', 'VARCHAR(20) DEFAULT \'\''),
            ('data_nascimento', 'DATE'),
            ('profissao', 'VARCHAR(100) DEFAULT \'\''),
            ('renda_mensal', 'DECIMAL(10, 2)'),
            ('observacoes', 'TEXT DEFAULT \'\''),
            ('ativo', 'BOOLEAN DEFAULT TRUE'),
            ('data_cadastro', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
            ('data_atualizacao', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
            ('email_verificado', 'BOOLEAN DEFAULT FALSE'),
            ('token_verificacao', 'VARCHAR(100) DEFAULT \'\''),
            ('codigo_verificacao', 'VARCHAR(6) DEFAULT \'\''),
            ('codigo_verificacao_expira', 'TIMESTAMP WITH TIME ZONE'),
            ('schema_name', 'VARCHAR(20) DEFAULT \'\''),
            ('criado_em', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
            ('atualizado_em', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
        ]
        
        for field_name, field_definition in additional_fields:
            try:
                cursor.execute(f"""
                    ALTER TABLE auth_user_custom 
                    ADD COLUMN IF NOT EXISTS {field_name} {field_definition};
                """)
                print(f"  ✅ Campo {field_name} adicionado")
            except Exception as e:
                print(f"  ⚠️ Campo {field_name}: {e}")
        
        # Verificar se todos os campos necessários existem
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = 'auth_user_custom'
            ORDER BY ordinal_position;
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Campos existentes na tabela ({len(existing_columns)}):")
        for col in existing_columns:
            print(f"  - {col}")
        
        # Verificar campos obrigatórios do modelo Django
        required_fields = [
            'id', 'password', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login',
            'tipo_pessoa', 'cpf', 'cnpj', 'razao_social', 'nome_fantasia',
            'endereco_logradouro', 'endereco_numero', 'endereco_complemento',
            'endereco_bairro', 'endereco_municipio', 'endereco_uf', 'endereco_cep',
            'telefone', 'celular', 'data_nascimento', 'profissao', 'renda_mensal',
            'observacoes', 'ativo', 'data_cadastro', 'data_atualizacao',
            'email_verificado', 'token_verificacao', 'codigo_verificacao',
            'codigo_verificacao_expira', 'schema_name', 'criado_em', 'atualizado_em'
        ]
        
        missing_fields = [field for field in required_fields if field not in existing_columns]
        
        if missing_fields:
            print(f"\n⚠️ Campos ainda faltantes: {missing_fields}")
        else:
            print("\n✅ Todos os campos necessários estão presentes!")
        
        print("\n🎉 Tabela auth_user_custom completamente atualizada!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    complete_customuser_table()
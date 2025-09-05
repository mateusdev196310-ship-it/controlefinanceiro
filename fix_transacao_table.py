import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_transacao_table():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando campos faltantes na tabela financas_transacao...")
        
        # Lista de campos para adicionar
        fields_to_add = [
            ('responsavel', 'VARCHAR(100)'),
            ('eh_parcelada', 'BOOLEAN DEFAULT FALSE'),
            ('transacao_pai_id', 'INTEGER REFERENCES financas_transacao(id)'),
            ('numero_parcela', 'INTEGER'),
            ('total_parcelas', 'INTEGER'),
            ('despesa_parcelada_id', 'INTEGER REFERENCES financas_despesaparcelada(id)'),
            ('pago', 'BOOLEAN DEFAULT FALSE'),
            ('data_pagamento', 'DATE')
        ]
        
        for field_name, field_definition in fields_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE financas_transacao 
                    ADD COLUMN IF NOT EXISTS {field_name} {field_definition};
                """)
                print(f"  ✅ Campo {field_name} adicionado")
            except Exception as e:
                print(f"  ⚠️ Campo {field_name}: {e}")
        
        # Verificar estrutura final da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_transacao'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Estrutura final da tabela financas_transacao ({len(columns)} campos):")
        for column_name, data_type, nullable, default in columns:
            print(f"  - {column_name}: {data_type} (nullable: {nullable}, default: {default})")
        
        # Verificar se há registros na tabela
        cursor.execute("SELECT COUNT(*) FROM financas_transacao;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros na tabela: {count}")
        
        print("\n🎉 Tabela financas_transacao atualizada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_transacao_table()
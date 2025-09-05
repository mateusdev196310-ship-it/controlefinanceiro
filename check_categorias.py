import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Categoria

print('=== CATEGORIAS NO BANCO ===')
categorias = Categoria.objects.all()
print(f'Total de categorias: {categorias.count()}')
print()

for cat in categorias:
    print(f'ID: {cat.id}')
    print(f'Nome: {cat.nome}')
    print(f'Cor: {cat.cor}')
    print(f'Tipo: {cat.tipo}')
    print('-' * 30)

if categorias.count() == 0:
    print('PROBLEMA: Nenhuma categoria encontrada no banco!')
    print('Vamos verificar se há dados na tabela...')
    
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM financas_categoria")
        count = cursor.fetchone()[0]
        print(f'Contagem direta na tabela: {count}')
        
        if count > 0:
            cursor.execute("SELECT id, nome, cor, tipo FROM financas_categoria LIMIT 10")
            rows = cursor.fetchall()
            print('Primeiras 10 categorias (consulta direta):')
            for row in rows:
                print(f'ID: {row[0]}, Nome: {row[1]}, Cor: {row[2]}, Tipo: {row[3]}')
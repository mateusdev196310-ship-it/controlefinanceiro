import os
import sys
import django
from datetime import date
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection
from financas.models import DespesaParcelada, Categoria, Conta

def test_simple_creation():
    print("=== Teste Simples de Criação de Despesa Parcelada ===")
    
    # Definir tenant_id manualmente
    connection.tenant_id = 5
    print(f"Connection tenant_id: {getattr(connection, 'tenant_id', 'Não definido')}")
    
    try:
        # Buscar categoria e conta existentes
        categoria = Categoria.objects.first()
        conta = Conta.objects.first()
        
        if not categoria:
            print("Erro: Nenhuma categoria encontrada")
            return
        if not conta:
            print("Erro: Nenhuma conta encontrada")
            return
            
        print(f"Categoria: {categoria.nome} (ID: {categoria.id})")
        print(f"Conta: {conta.nome} (ID: {conta.id})")
        
        # Criar despesa parcelada sem gerar parcelas ainda
        despesa = DespesaParcelada.objects.create(
            descricao="Teste Simples",
            valor_total=Decimal('1000.00'),
            categoria=categoria,
            numero_parcelas=5,
            data_primeira_parcela=date(2025, 2, 1),
            conta=conta,
            responsavel="Teste"
        )
        
        print(f"\nDespesa criada:")
        print(f"ID: {despesa.id}")
        print(f"Descrição: {despesa.descricao}")
        print(f"Tenant ID: {despesa.tenant_id}")
        print(f"Parcelas geradas: {despesa.parcelas_geradas}")
        
        # Agora tentar gerar as parcelas
        print("\nGerando parcelas...")
        despesa.gerar_parcelas()
        
        print(f"Parcelas geradas: {despesa.parcelas_geradas}")
        
        # Verificar parcelas criadas
        parcelas = despesa.get_parcelas()
        print(f"Número de parcelas criadas: {parcelas.count()}")
        
        for parcela in parcelas:
            print(f"Parcela {parcela.numero_parcela}: {parcela.descricao} - Tenant ID: {parcela.tenant_id}")
            
    except Exception as e:
        print(f"Erro durante criação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_creation()
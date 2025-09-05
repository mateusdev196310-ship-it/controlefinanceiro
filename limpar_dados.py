import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Transacao, Conta, DespesaParcelada, FechamentoMensal, Categoria, Meta

print("🧹 Iniciando limpeza dos dados...")
print()

# Contar registros antes da limpeza
print("📊 Dados antes da limpeza:")
print(f"  Transações: {Transacao.objects.count()}")
print(f"  Contas: {Conta.objects.count()}")
print(f"  Despesas Parceladas: {DespesaParcelada.objects.count()}")
print(f"  Fechamentos Mensais: {FechamentoMensal.objects.count()}")
print(f"  Categorias: {Categoria.objects.count()}")
print(f"  Metas: {Meta.objects.count()}")
print()

# Deletar todos os registros
print("🗑️ Removendo dados...")

# Deletar transações
transacoes_deletadas = Transacao.objects.all().delete()[0]
print(f"  ✅ {transacoes_deletadas} transações removidas")

# Deletar contas
contas_deletadas = Conta.objects.all().delete()[0]
print(f"  ✅ {contas_deletadas} contas removidas")

# Deletar despesas parceladas
despesas_deletadas = DespesaParcelada.objects.all().delete()[0]
print(f"  ✅ {despesas_deletadas} despesas parceladas removidas")

# Deletar fechamentos mensais
fechamentos_deletados = FechamentoMensal.objects.all().delete()[0]
print(f"  ✅ {fechamentos_deletados} fechamentos mensais removidos")

# Deletar metas
metas_deletadas = Meta.objects.all().delete()[0]
print(f"  ✅ {metas_deletadas} metas removidas")

# Manter categorias (são importantes para o funcionamento)
print(f"  ℹ️ Categorias mantidas: {Categoria.objects.count()}")

print()
print("📊 Dados após a limpeza:")
print(f"  Transações: {Transacao.objects.count()}")
print(f"  Contas: {Conta.objects.count()}")
print(f"  Despesas Parceladas: {DespesaParcelada.objects.count()}")
print(f"  Fechamentos Mensais: {FechamentoMensal.objects.count()}")
print(f"  Categorias: {Categoria.objects.count()}")
print(f"  Metas: {Meta.objects.count()}")
print()
print("✅ Limpeza concluída! Agora você pode começar do zero.")
print("💡 Dica: Crie suas contas primeiro, depois adicione transações.")
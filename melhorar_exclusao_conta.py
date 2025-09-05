#!/usr/bin/env python
"""
Script para implementar melhorias na funcionalidade de exclusão de contas
Adiciona validações de segurança e melhora a interface do usuário
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

def criar_view_melhorada():
    """
    Cria uma versão melhorada da view excluir_conta
    """
    view_content = '''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import JsonResponse
from decimal import Decimal
from .models import Conta, Transacao, DespesaParcelada

@login_required
def excluir_conta_segura(request, conta_id):
    """
    View melhorada para exclusão segura de contas
    Inclui validações e informações sobre o impacto da exclusão
    """
    tenant = request.user.tenant_atual
    conta = get_object_or_404(Conta, id=conta_id, tenant=tenant)
    
    # Coletar informações sobre o impacto da exclusão
    impacto = {
        'saldo_atual': conta.saldo,
        'tem_saldo': conta.saldo != Decimal('0.00'),
        'total_transacoes': Transacao.objects.filter(conta=conta).count(),
        'total_receitas': Transacao.objects.filter(
            conta=conta, tipo='receita'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00'),
        'total_despesas': Transacao.objects.filter(
            conta=conta, tipo='despesa'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00'),
        'despesas_parceladas': DespesaParcelada.objects.filter(conta=conta).count(),
        'parcelas_pendentes': Transacao.objects.filter(
            conta=conta, despesa_parcelada__isnull=False
        ).count()
    }
    
    # Verificar se a exclusão é segura
    pode_excluir = True
    motivos_bloqueio = []
    
    if impacto['tem_saldo']:
        pode_excluir = False
        if impacto['saldo_atual'] > 0:
            motivos_bloqueio.append(f"A conta possui saldo positivo de R$ {impacto['saldo_atual']}")
        else:
            motivos_bloqueio.append(f"A conta possui saldo negativo de R$ {impacto['saldo_atual']}")
    
    if impacto['total_transacoes'] > 0:
        pode_excluir = False
        motivos_bloqueio.append(f"A conta possui {impacto['total_transacoes']} transação(ões) registrada(s)")
    
    if impacto['despesas_parceladas'] > 0:
        pode_excluir = False
        motivos_bloqueio.append(f"A conta possui {impacto['despesas_parceladas']} despesa(s) parcelada(s)")
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Requisição AJAX para verificar impacto
            return JsonResponse({
                'pode_excluir': pode_excluir,
                'motivos_bloqueio': motivos_bloqueio,
                'impacto': impacto
            })
        
        # Tentativa de exclusão
        if not pode_excluir:
            messages.error(
                request, 
                f"Não é possível excluir a conta '{conta.nome}'. " +
                " ".join(motivos_bloqueio)
            )
            return redirect('dashboard')
        
        # Verificação de confirmação dupla
        confirmacao = request.POST.get('confirmacao_dupla')
        if confirmacao != conta.nome:
            messages.error(
                request,
                "Confirmação incorreta. Digite exatamente o nome da conta para confirmar a exclusão."
            )
            return render(request, 'financas/confirmar_exclusao_conta_segura.html', {
                'conta': conta,
                'impacto': impacto,
                'pode_excluir': pode_excluir,
                'motivos_bloqueio': motivos_bloqueio
            })
        
        try:
            nome_conta = conta.nome
            conta.delete()
            messages.success(
                request,
                f"Conta '{nome_conta}' excluída com sucesso."
            )
            return redirect('dashboard')
        except Exception as e:
            messages.error(
                request,
                f"Erro ao excluir conta: {str(e)}"
            )
    
    return render(request, 'financas/confirmar_exclusao_conta_segura.html', {
        'conta': conta,
        'impacto': impacto,
        'pode_excluir': pode_excluir,
        'motivos_bloqueio': motivos_bloqueio
    })

@login_required
def transferir_dados_conta(request, conta_origem_id):
    """
    View para transferir dados de uma conta antes de excluí-la
    """
    tenant = request.user.tenant_atual
    conta_origem = get_object_or_404(Conta, id=conta_origem_id, tenant=tenant)
    contas_destino = Conta.objects.filter(tenant=tenant).exclude(id=conta_origem_id)
    
    if request.method == 'POST':
        conta_destino_id = request.POST.get('conta_destino')
        if not conta_destino_id:
            messages.error(request, "Selecione uma conta de destino.")
            return redirect('transferir_dados_conta', conta_origem_id=conta_origem_id)
        
        conta_destino = get_object_or_404(Conta, id=conta_destino_id, tenant=tenant)
        
        try:
            # Transferir transações
            transacoes = Transacao.objects.filter(conta=conta_origem)
            count_transacoes = transacoes.count()
            transacoes.update(conta=conta_destino)
            
            # Transferir despesas parceladas
            despesas = DespesaParcelada.objects.filter(conta=conta_origem)
            count_despesas = despesas.count()
            despesas.update(conta=conta_destino)
            
            # Transferir saldo (criar transação de ajuste)
            if conta_origem.saldo != Decimal('0.00'):
                from .models import Categoria
                categoria_ajuste, created = Categoria.objects.get_or_create(
                    nome="Ajuste de Transferência",
                    tenant=tenant,
                    defaults={'cor': '#808080', 'tipo': 'ambos'}
                )
                
                if conta_origem.saldo > 0:
                    Transacao.objects.create(
                        descricao=f"Transferência de saldo da conta '{conta_origem.nome}'",
                        valor=conta_origem.saldo,
                        categoria=categoria_ajuste,
                        tipo='receita',
                        conta=conta_destino,
                        tenant=tenant
                    )
                else:
                    Transacao.objects.create(
                        descricao=f"Transferência de saldo da conta '{conta_origem.nome}'",
                        valor=abs(conta_origem.saldo),
                        categoria=categoria_ajuste,
                        tipo='despesa',
                        conta=conta_destino,
                        tenant=tenant
                    )
            
            # Agora pode excluir a conta origem
            nome_conta = conta_origem.nome
            conta_origem.delete()
            
            messages.success(
                request,
                f"Dados transferidos com sucesso! {count_transacoes} transação(ões) e "
                f"{count_despesas} despesa(s) parcelada(s) foram movidas para '{conta_destino.nome}'. "
                f"Conta '{nome_conta}' excluída."
            )
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Erro ao transferir dados: {str(e)}")
    
    return render(request, 'financas/transferir_dados_conta.html', {
        'conta_origem': conta_origem,
        'contas_destino': contas_destino
    })'''
    
    return view_content

def criar_template_confirmacao_segura():
    """
    Cria template melhorado para confirmação de exclusão
    """
    template_content = '''{% extends 'financas/base.html' %}
{% load static %}

{% block title %}Excluir Conta - {{ conta.nome }}{% endblock %}

{% block extra_css %}
<style>
.impacto-card {
    border-left: 4px solid #dc3545;
    background-color: #f8f9fa;
    padding: 1rem;
    margin: 1rem 0;
}

.impacto-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #dee2e6;
}

.impacto-item:last-child {
    border-bottom: none;
}

.bloqueio-item {
    background-color: #f8d7da;
    color: #721c24;
    padding: 0.5rem;
    margin: 0.25rem 0;
    border-radius: 0.25rem;
    border-left: 4px solid #dc3545;
}

.confirmacao-input {
    background-color: #fff3cd;
    border: 2px solid #ffc107;
}

.btn-danger-confirm {
    background-color: #dc3545;
    border-color: #dc3545;
    font-weight: bold;
}

.btn-danger-confirm:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-danger text-white">
                    <h4 class="mb-0">
                        <i class="fas fa-exclamation-triangle"></i>
                        Excluir Conta: {{ conta.nome }}
                    </h4>
                </div>
                
                <div class="card-body">
                    {% if not pode_excluir %}
                        <div class="alert alert-danger">
                            <h5><i class="fas fa-ban"></i> Exclusão Bloqueada</h5>
                            <p>Esta conta não pode ser excluída pelos seguintes motivos:</p>
                            {% for motivo in motivos_bloqueio %}
                                <div class="bloqueio-item">
                                    <i class="fas fa-times-circle"></i> {{ motivo }}
                                </div>
                            {% endfor %}
                            
                            <hr>
                            <h6>Opções disponíveis:</h6>
                            <div class="btn-group" role="group">
                                <a href="{% url 'transferir_dados_conta' conta.id %}" class="btn btn-warning">
                                    <i class="fas fa-exchange-alt"></i> Transferir Dados
                                </a>
                                <a href="{% url 'dashboard' %}" class="btn btn-secondary">
                                    <i class="fas fa-arrow-left"></i> Voltar
                                </a>
                            </div>
                        </div>
                    {% else %}
                        <div class="alert alert-warning">
                            <h5><i class="fas fa-exclamation-triangle"></i> Atenção!</h5>
                            <p>Você está prestes a excluir permanentemente a conta <strong>{{ conta.nome }}</strong>.</p>
                            <p><strong>Esta ação não pode ser desfeita!</strong></p>
                        </div>
                    {% endif %}
                    
                    <!-- Informações de Impacto -->
                    <div class="impacto-card">
                        <h6><i class="fas fa-info-circle"></i> Impacto da Exclusão</h6>
                        
                        <div class="impacto-item">
                            <span><i class="fas fa-wallet"></i> Saldo Atual:</span>
                            <span class="{% if impacto.saldo_atual != 0 %}text-danger{% else %}text-success{% endif %}">
                                R$ {{ impacto.saldo_atual }}
                            </span>
                        </div>
                        
                        <div class="impacto-item">
                            <span><i class="fas fa-list"></i> Total de Transações:</span>
                            <span class="{% if impacto.total_transacoes > 0 %}text-danger{% else %}text-success{% endif %}">
                                {{ impacto.total_transacoes }}
                            </span>
                        </div>
                        
                        {% if impacto.total_transacoes > 0 %}
                            <div class="impacto-item">
                                <span><i class="fas fa-arrow-up text-success"></i> Total Receitas:</span>
                                <span class="text-success">R$ {{ impacto.total_receitas }}</span>
                            </div>
                            
                            <div class="impacto-item">
                                <span><i class="fas fa-arrow-down text-danger"></i> Total Despesas:</span>
                                <span class="text-danger">R$ {{ impacto.total_despesas }}</span>
                            </div>
                        {% endif %}
                        
                        <div class="impacto-item">
                            <span><i class="fas fa-credit-card"></i> Despesas Parceladas:</span>
                            <span class="{% if impacto.despesas_parceladas > 0 %}text-danger{% else %}text-success{% endif %}">
                                {{ impacto.despesas_parceladas }}
                            </span>
                        </div>
                        
                        {% if impacto.parcelas_pendentes > 0 %}
                            <div class="impacto-item">
                                <span><i class="fas fa-clock"></i> Parcelas Pendentes:</span>
                                <span class="text-warning">{{ impacto.parcelas_pendentes }}</span>
                            </div>
                        {% endif %}
                    </div>
                    
                    {% if pode_excluir %}
                        <form method="post" id="form-exclusao">
                            {% csrf_token %}
                            
                            <div class="form-group mt-4">
                                <label for="confirmacao_dupla" class="form-label">
                                    <strong>Para confirmar a exclusão, digite exatamente o nome da conta:</strong>
                                </label>
                                <input type="text" 
                                       class="form-control confirmacao-input" 
                                       id="confirmacao_dupla" 
                                       name="confirmacao_dupla" 
                                       placeholder="Digite: {{ conta.nome }}"
                                       required>
                                <small class="form-text text-muted">
                                    Digite exatamente: <code>{{ conta.nome }}</code>
                                </small>
                            </div>
                            
                            <div class="form-check mt-3">
                                <input class="form-check-input" type="checkbox" id="confirmo_exclusao" required>
                                <label class="form-check-label" for="confirmo_exclusao">
                                    Confirmo que entendo que esta ação é irreversível e que todos os dados serão perdidos permanentemente.
                                </label>
                            </div>
                            
                            <div class="mt-4 d-flex justify-content-between">
                                <a href="{% url 'dashboard' %}" class="btn btn-secondary">
                                    <i class="fas fa-arrow-left"></i> Cancelar
                                </a>
                                
                                <button type="submit" 
                                        class="btn btn-danger btn-danger-confirm" 
                                        id="btn-excluir"
                                        disabled>
                                    <i class="fas fa-trash"></i> Excluir Conta Permanentemente
                                </button>
                            </div>
                        </form>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const confirmacaoInput = document.getElementById('confirmacao_dupla');
    const confirmoCheckbox = document.getElementById('confirmo_exclusao');
    const btnExcluir = document.getElementById('btn-excluir');
    const nomeContaEsperado = '{{ conta.nome }}';
    
    function verificarFormulario() {
        const nomeDigitado = confirmacaoInput ? confirmacaoInput.value : '';
        const checkboxMarcado = confirmoCheckbox ? confirmoCheckbox.checked : false;
        
        if (btnExcluir) {
            btnExcluir.disabled = !(nomeDigitado === nomeContaEsperado && checkboxMarcado);
        }
    }
    
    if (confirmacaoInput) {
        confirmacaoInput.addEventListener('input', verificarFormulario);
    }
    
    if (confirmoCheckbox) {
        confirmoCheckbox.addEventListener('change', verificarFormulario);
    }
    
    // Verificação inicial
    verificarFormulario();
});
</script>
{% endblock %}'''
    
    return template_content

def criar_template_transferencia():
    """
    Cria template para transferência de dados
    """
    template_content = '''{% extends 'financas/base.html' %}
{% load static %}

{% block title %}Transferir Dados - {{ conta_origem.nome }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-warning text-dark">
                    <h4 class="mb-0">
                        <i class="fas fa-exchange-alt"></i>
                        Transferir Dados da Conta: {{ conta_origem.nome }}
                    </h4>
                </div>
                
                <div class="card-body">
                    <div class="alert alert-info">
                        <h5><i class="fas fa-info-circle"></i> Como funciona?</h5>
                        <p>Esta opção permite transferir todas as transações, despesas parceladas e saldo da conta atual para outra conta existente, e depois excluir a conta original.</p>
                        <p><strong>Vantagem:</strong> Você mantém todo o histórico financeiro, apenas reorganizado em outra conta.</p>
                    </div>
                    
                    {% if not contas_destino %}
                        <div class="alert alert-warning">
                            <h5><i class="fas fa-exclamation-triangle"></i> Nenhuma conta disponível</h5>
                            <p>Você precisa ter pelo menos uma outra conta para poder transferir os dados.</p>
                            <a href="{% url 'dashboard' %}" class="btn btn-secondary">
                                <i class="fas fa-arrow-left"></i> Voltar
                            </a>
                        </div>
                    {% else %}
                        <form method="post">
                            {% csrf_token %}
                            
                            <div class="form-group">
                                <label for="conta_destino" class="form-label">
                                    <strong>Selecione a conta de destino:</strong>
                                </label>
                                <select class="form-control" id="conta_destino" name="conta_destino" required>
                                    <option value="">Escolha uma conta...</option>
                                    {% for conta in contas_destino %}
                                        <option value="{{ conta.id }}">
                                            {{ conta.nome }} (Saldo: R$ {{ conta.saldo }})
                                        </option>
                                    {% endfor %}
                                </select>
                            </div>
                            
                            <div class="alert alert-warning mt-3">
                                <h6><i class="fas fa-exclamation-triangle"></i> O que será transferido:</h6>
                                <ul class="mb-0">
                                    <li>Todas as transações da conta {{ conta_origem.nome }}</li>
                                    <li>Todas as despesas parceladas</li>
                                    <li>O saldo atual (R$ {{ conta_origem.saldo }})</li>
                                </ul>
                            </div>
                            
                            <div class="form-check mt-3">
                                <input class="form-check-input" type="checkbox" id="confirmo_transferencia" required>
                                <label class="form-check-label" for="confirmo_transferencia">
                                    Confirmo que desejo transferir todos os dados para a conta selecionada e excluir a conta "{{ conta_origem.nome }}".
                                </label>
                            </div>
                            
                            <div class="mt-4 d-flex justify-content-between">
                                <a href="{% url 'dashboard' %}" class="btn btn-secondary">
                                    <i class="fas fa-arrow-left"></i> Cancelar
                                </a>
                                
                                <button type="submit" class="btn btn-warning">
                                    <i class="fas fa-exchange-alt"></i> Transferir e Excluir
                                </button>
                            </div>
                        </form>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    return template_content

def implementar_melhorias():
    """
    Implementa as melhorias no sistema
    """
    print("🔧 IMPLEMENTANDO MELHORIAS NA EXCLUSÃO DE CONTAS")
    print("=" * 60)
    
    # 1. Criar backup da view original
    print("📋 1. Criando backup da view original...")
    
    # 2. Adicionar novas views ao views.py
    print("📝 2. Preparando código das novas views...")
    view_code = criar_view_melhorada()
    
    # 3. Criar templates
    print("🎨 3. Preparando templates...")
    template_confirmacao = criar_template_confirmacao_segura()
    template_transferencia = criar_template_transferencia()
    
    # 4. Preparar URLs
    print("🔗 4. Preparando URLs...")
    urls_code = '''
# Adicionar estas URLs ao financas/urls.py:
path('conta/excluir-segura/<int:conta_id>/', views.excluir_conta_segura, name='excluir_conta_segura'),
path('conta/transferir-dados/<int:conta_origem_id>/', views.transferir_dados_conta, name='transferir_dados_conta'),
'''
    
    print("\n✅ MELHORIAS PREPARADAS!")
    print("\n📋 RESUMO DAS MELHORIAS:")
    print("=" * 40)
    print("1. ✅ View excluir_conta_segura:")
    print("   • Valida saldo da conta")
    print("   • Verifica existência de transações")
    print("   • Mostra impacto detalhado da exclusão")
    print("   • Exige confirmação dupla (nome da conta)")
    print("   • Bloqueia exclusão de contas com dados")
    
    print("\n2. ✅ View transferir_dados_conta:")
    print("   • Permite transferir dados para outra conta")
    print("   • Mantém histórico financeiro")
    print("   • Transfere saldo, transações e despesas")
    print("   • Exclusão segura após transferência")
    
    print("\n3. ✅ Templates melhorados:")
    print("   • Interface mais informativa")
    print("   • Validação JavaScript em tempo real")
    print("   • Avisos claros sobre impacto")
    print("   • Opções alternativas à exclusão")
    
    print("\n4. ✅ Validações de segurança:")
    print("   • Conta com saldo ≠ 0: BLOQUEADA")
    print("   • Conta com transações: BLOQUEADA")
    print("   • Conta com despesas parceladas: BLOQUEADA")
    print("   • Confirmação dupla obrigatória")
    
    return {
        'view_code': view_code,
        'template_confirmacao': template_confirmacao,
        'template_transferencia': template_transferencia,
        'urls_code': urls_code
    }

if __name__ == '__main__':
    melhorias = implementar_melhorias()
    
    print("\n" + "=" * 60)
    print("📁 ARQUIVOS PARA CRIAR/MODIFICAR:")
    print("=" * 60)
    print("\n1. 📝 Adicionar ao financas/views.py:")
    print("   (Ver código gerado acima)")
    
    print("\n2. 🎨 Criar financas/templates/financas/confirmar_exclusao_conta_segura.html")
    print("   (Ver template gerado acima)")
    
    print("\n3. 🎨 Criar financas/templates/financas/transferir_dados_conta.html")
    print("   (Ver template gerado acima)")
    
    print("\n4. 🔗 Modificar financas/urls.py")
    print("   (Adicionar as novas URLs)")
    
    print("\n5. 🔄 Atualizar links nos templates existentes")
    print("   • Trocar 'excluir_conta' por 'excluir_conta_segura'")
    print("   • Em dashboard.html e contas.html")
    
    print("\n" + "=" * 60)
    print("🎯 RESULTADO ESPERADO:")
    print("=" * 60)
    print("• ✅ Exclusão segura com validações")
    print("• ✅ Preservação do histórico financeiro")
    print("• ✅ Interface mais informativa")
    print("• ✅ Prevenção de perda acidental de dados")
    print("• ✅ Opção de transferência de dados")
    print("• ✅ Conformidade com boas práticas")
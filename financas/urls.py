from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/modern/', views.dashboard_modern, name='dashboard_modern'),
    path('', views.home_view, name='home'),
    path('transacoes/', views.transacoes, name='transacoes'),
    path('transacoes/criar/', views.adicionar_transacao, name='transacao_create'),
    path('transacoes/editar/<int:transacao_id>/', views.adicionar_transacao, name='transacao_update'),
    path('transacoes/excluir/<int:transacao_id>/', views.excluir_transacao, name='excluir_transacao'),
    path('categorias/', views.categorias, name='categorias'),
    path('categorias/criar/', views.adicionar_categoria, name='categoria_create'),
    path('adicionar-categoria/', views.adicionar_categoria, name='adicionar_categoria'),
    path('categorias/editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/excluir/<int:categoria_id>/', views.excluir_categoria, name='excluir_categoria'),
    path('adicionar-despesa-parcelada/', views.adicionar_despesa_parcelada, name='adicionar_despesa_parcelada'),
    path('despesas-parceladas/', views.despesas_parceladas, name='despesas_parceladas'),
    path('despesa-parcelada/<int:despesa_id>/', views.detalhes_despesa_parcelada, name='detalhes_despesa_parcelada'),
    path('despesa-parcelada/excluir/<int:despesa_id>/', views.excluir_despesa_parcelada, name='excluir_despesa_parcelada'),
    path('despesa-parcelada/gerar-parcelas/<int:despesa_id>/', views.gerar_parcelas_despesa, name='gerar_parcelas_despesa'),
    path('parcela/marcar-paga/<int:parcela_id>/', views.marcar_parcela_paga, name='marcar_parcela_paga'),
    path('parcela/marcar-nao-paga/<int:parcela_id>/', views.marcar_parcela_nao_paga, name='marcar_parcela_nao_paga'),
    path('parcela/<int:parcela_id>/pagar/', views.processar_pagamento_parcela, name='processar_pagamento_parcela'),
    path('contas/', views.contas, name='contas'),
    path('contas/criar/', views.criar_conta, name='conta_create'),
    path('contas/editar/<int:conta_id>/', views.editar_conta, name='editar_conta'),
    path('contas/excluir/<int:conta_id>/', views.excluir_conta, name='excluir_conta'),
    path('contas/excluir-segura/<int:conta_id>/', views.excluir_conta_segura, name='excluir_conta_segura'),
    path('contas/transferir-dados/<int:conta_origem_id>/', views.transferir_dados_conta, name='transferir_dados_conta'),
    path('relatorios/', views.relatorios, name='relatorios'),

    # Rotas de fechamento mensal removidas - agora o fechamento é automático
    path('test-filter/', views.test_filter, name='test_filter'),
    # API endpoints
    path('api/resumo-financeiro/', views.api_resumo_financeiro, name='api_resumo_financeiro'),
    path('api/transacoes-por-categoria/', views.api_transacoes_por_categoria, name='api_transacoes_por_categoria'),
    path('api/evolucao-saldo/', views.api_evolucao_saldo, name='api_evolucao_saldo'),
    path('api/transacoes-recentes/', views.api_transacoes_recentes, name='api_transacoes_recentes'),
    path('compartilhar-whatsapp/', views.compartilhar_whatsapp, name='compartilhar_whatsapp'),
    # URLs de registro e autenticação
    path('registro/', views.registro_view, name='registro'),
    path('verificar-codigo/', views.verificar_codigo_view, name='verificar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo_view, name='reenviar_codigo'),
    path('confirmar-email/<str:token>/', views.confirmar_email_view, name='confirmar_email'),
    path('buscar-cnpj/', views.buscar_cnpj_view, name='buscar_cnpj'),
    # URLs de recuperação de senha
    path('esqueci-senha/', views.esqueci_senha_view, name='esqueci_senha'),
    path('reset-senha/<str:token>/', views.reset_senha_view, name='reset_senha'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
]
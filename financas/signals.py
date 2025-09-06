from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transacao, CustomUser, Categoria, Tenant
import logging
import threading

logger = logging.getLogger(__name__)

# Thread-local storage para controlar quando não atualizar saldo
_thread_local = threading.local()

def desabilitar_atualizacao_saldo():
    """Desabilita a atualização automática de saldo pelos signals."""
    _thread_local.skip_saldo_update = True

def habilitar_atualizacao_saldo():
    """Habilita a atualização automática de saldo pelos signals."""
    _thread_local.skip_saldo_update = False

@receiver(post_save, sender=Transacao)
def atualizar_saldo_conta_apos_salvar(sender, instance, created, **kwargs):
    """
    Atualiza o saldo da conta automaticamente após criar ou editar uma transação.
    
    Args:
        sender: O modelo que enviou o signal (Transacao)
        instance: A instância da transação que foi salva
        created: Boolean indicando se a transação foi criada (True) ou editada (False)
        **kwargs: Argumentos adicionais do signal
    """
    try:
        # Verificar se deve pular a atualização de saldo
        if getattr(_thread_local, 'skip_saldo_update', False):
            return
            
        # Atualizar saldo da conta relacionada à transação
        instance.conta.atualizar_saldo()
        
        # Log da operação para auditoria
        action = "criada" if created else "editada"
        logger.info(
            f"Transação {action}: {instance.descricao} - "
            f"R$ {instance.valor} ({instance.tipo}) - "
            f"Conta: {instance.conta.nome} - "
            f"Novo saldo: R$ {instance.conta.saldo}"
        )
        
    except Exception as e:
        logger.error(
            f"Erro ao atualizar saldo da conta {instance.conta.nome} "
            f"após salvar transação {instance.id}: {str(e)}"
        )
        # Re-raise a exceção para não mascarar problemas
        raise

@receiver(post_save, sender=CustomUser)
def criar_categorias_padrao_usuario(sender, instance, created, **kwargs):
    """
    Cria categorias padrão automaticamente quando um usuário é ativado.
    
    Args:
        sender: O modelo que enviou o signal (CustomUser)
        instance: A instância do usuário que foi salva
        created: Boolean indicando se o usuário foi criado (True) ou editado (False)
        **kwargs: Argumentos adicionais do signal
    """
    try:
        # Só criar categorias se o usuário foi ativado (is_active=True e email_verificado=True)
        if instance.is_active and instance.email_verificado:
            # Criar ou obter o Tenant do usuário
            tenant, tenant_created = Tenant.objects.get_or_create(
                id=instance.id,
                defaults={
                    'nome': f'Tenant for {instance.username}',
                    'codigo': f'U{instance.id}',  # Código mais curto usando ID
                    'ativo': True
                }
            )
            
            # Associar usuário ao tenant se não estiver associado
            if instance not in tenant.usuarios.all():
                tenant.usuarios.add(instance)
            
            # Verificar se já existem categorias para este tenant
            categorias_existentes = Categoria.objects.filter(tenant_id=tenant.id).count()
            
            if categorias_existentes == 0:
                # Definir categorias padrão
                categorias_padrao = [
                    {'nome': 'Alimentação', 'cor': '#FF6B6B', 'tipo': 'despesa'},
                    {'nome': 'Transporte', 'cor': '#4ECDC4', 'tipo': 'despesa'},
                    {'nome': 'Moradia', 'cor': '#45B7D1', 'tipo': 'despesa'},
                    {'nome': 'Saúde', 'cor': '#96CEB4', 'tipo': 'despesa'},
                    {'nome': 'Educação', 'cor': '#FFEAA7', 'tipo': 'despesa'},
                    {'nome': 'Lazer', 'cor': '#DDA0DD', 'tipo': 'despesa'},
                    {'nome': 'Compras', 'cor': '#98D8C8', 'tipo': 'despesa'},
                    {'nome': 'Contas Fixas', 'cor': '#F7DC6F', 'tipo': 'despesa'},
                    {'nome': 'Salário', 'cor': '#52C41A', 'tipo': 'receita'},
                    {'nome': 'Freelance', 'cor': '#1890FF', 'tipo': 'receita'},
                    {'nome': 'Investimentos', 'cor': '#722ED1', 'tipo': 'receita'},
                    {'nome': 'Outros', 'cor': '#8C8C8C', 'tipo': 'despesa'},
                ]
                
                # Criar categorias
                categorias_criadas = 0
                for categoria_data in categorias_padrao:
                    categoria = Categoria.objects.create(
                        nome=categoria_data['nome'],
                        cor=categoria_data['cor'],
                        tipo=categoria_data['tipo'],
                        tenant_id=tenant.id
                    )
                    categorias_criadas += 1
                
                logger.info(
                    f"Categorias padrão criadas para usuário {instance.username}: "
                    f"{categorias_criadas} categorias"
                )
                
    except Exception as e:
        logger.error(
            f"Erro ao criar categorias padrão para usuário {instance.username}: {str(e)}"
        )
        # Não re-raise para não interromper o processo de ativação do usuário

@receiver(post_delete, sender=Transacao)
def atualizar_saldo_conta_apos_deletar(sender, instance, **kwargs):
    """
    Atualiza o saldo da conta automaticamente após deletar uma transação.
    
    Args:
        sender: O modelo que enviou o signal (Transacao)
        instance: A instância da transação que foi deletada
        **kwargs: Argumentos adicionais do signal
    """
    try:
        # Verificar se deve pular a atualização de saldo
        if getattr(_thread_local, 'skip_saldo_update', False):
            return
        # Atualizar saldo da conta relacionada à transação deletada
        instance.conta.atualizar_saldo()
        
        # Log da operação para auditoria
        logger.info(
            f"Transação deletada: {instance.descricao} - "
            f"R$ {instance.valor} ({instance.tipo}) - "
            f"Conta: {instance.conta.nome} - "
            f"Novo saldo: R$ {instance.conta.saldo}"
        )
        
    except Exception as e:
        logger.error(
            f"Erro ao atualizar saldo da conta {instance.conta.nome} "
            f"após deletar transação {instance.id}: {str(e)}"
        )
        # Re-raise a exceção para não mascarar problemas
        raise
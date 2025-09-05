from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transacao
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
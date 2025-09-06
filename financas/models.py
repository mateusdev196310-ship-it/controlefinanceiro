from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import connection
import re
import requests

from .constants import TipoTransacao, FormatConfig, ErrorMessages, ValidationConfig
from .exceptions import ValidationError as CustomValidationError
from .validators import django_validar_cpf, django_validar_cnpj, formatar_cpf, formatar_cnpj

class CustomUser(AbstractUser):
    """
    Modelo de usuário customizado com campos CPF/CNPJ para multi-tenancy.
    """
    TIPO_PESSOA_CHOICES = [
        ('fisica', 'Pessoa Física'),
        ('juridica', 'Pessoa Jurídica'),
    ]
    
    # Campos básicos
    tipo_pessoa = models.CharField(
        max_length=10,
        choices=TIPO_PESSOA_CHOICES,
        verbose_name='Tipo de Pessoa'
    )
    
    cpf = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        unique=True,
        validators=[django_validar_cpf],
        verbose_name='CPF',
        help_text='Apenas números ou formato XXX.XXX.XXX-XX'
    )
    
    cnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        unique=True,
        validators=[django_validar_cnpj],
        verbose_name='CNPJ',
        help_text='Apenas números ou formato XX.XXX.XXX/XXXX-XX'
    )
    
    # Campos para pessoa jurídica (preenchidos automaticamente via API Sefaz)
    razao_social = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Razão Social'
    )
    
    nome_fantasia = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nome Fantasia'
    )
    
    # Campos de endereço
    endereco_logradouro = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Logradouro'
    )
    
    endereco_numero = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número'
    )
    
    endereco_complemento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Complemento'
    )
    
    endereco_bairro = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Bairro'
    )
    
    endereco_municipio = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Município'
    )
    
    endereco_uf = models.CharField(
        max_length=2,
        blank=True,
        verbose_name='UF'
    )
    
    endereco_cep = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='CEP'
    )
    
    # Campos de contato
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefone'
    )
    
    # Campos de controle
    email_verificado = models.BooleanField(
        default=False,
        verbose_name='Email Verificado'
    )
    
    token_verificacao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Token de Verificação'
    )
    
    codigo_verificacao = models.CharField(
        max_length=6,
        blank=True,
        verbose_name='Código de Verificação'
    )
    
    codigo_verificacao_expira = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expiração do Código'
    )
    
    # Schema do banco de dados (será o CPF/CNPJ limpo)
    schema_name = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name='Nome do Schema'
    )
    
    # Campos de auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'auth_user_custom'
        # Evita conflitos com o modelo User padrão
        swappable = 'AUTH_USER_MODEL'
    
    def clean(self):
        """
        Validações customizadas do modelo.
        """
        super().clean()
        
        # Valida que pessoa física deve ter CPF
        if self.tipo_pessoa == 'fisica':
            if not self.cpf:
                raise ValidationError({'cpf': 'CPF é obrigatório para pessoa física.'})
            if self.cnpj:
                raise ValidationError({'cnpj': 'Pessoa física não pode ter CNPJ.'})
        
        # Valida que pessoa jurídica deve ter CNPJ
        elif self.tipo_pessoa == 'juridica':
            if not self.cnpj:
                raise ValidationError({'cnpj': 'CNPJ é obrigatório para pessoa jurídica.'})
            if self.cpf:
                raise ValidationError({'cpf': 'Pessoa jurídica não pode ter CPF.'})
        
        # Remove formatação dos documentos
        if self.cpf:
            self.cpf = re.sub(r'\D', '', self.cpf)
        if self.cnpj:
            self.cnpj = re.sub(r'\D', '', self.cnpj)
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para gerar o schema_name automaticamente.
        """
        # Gera o nome do schema baseado no CPF/CNPJ
        if not self.schema_name:
            if self.tipo_pessoa == 'fisica' and self.cpf:
                self.schema_name = f"user_{re.sub(r'\D', '', self.cpf)}"
            elif self.tipo_pessoa == 'juridica' and self.cnpj:
                self.schema_name = f"user_{re.sub(r'\D', '', self.cnpj)}"
        
        super().save(*args, **kwargs)
    
    def get_documento(self):
        """
        Retorna o documento principal (CPF ou CNPJ) do usuário.
        """
        if self.tipo_pessoa == 'fisica':
            return self.cpf
        elif self.tipo_pessoa == 'juridica':
            return self.cnpj
        return None
    
    def get_documento_formatado(self):
        """
        Retorna o documento principal formatado.
        """
        if self.tipo_pessoa == 'fisica' and self.cpf:
            return formatar_cpf(self.cpf)
        elif self.tipo_pessoa == 'juridica' and self.cnpj:
            return formatar_cnpj(self.cnpj)
        return None
    
    def get_nome_completo(self):
        """
        Retorna o nome completo do usuário (nome fantasia para PJ, nome completo para PF).
        """
        if self.tipo_pessoa == 'juridica':
            return self.nome_fantasia or self.razao_social or self.username
        else:
            return self.get_full_name() or self.username
    
    def __str__(self):
        documento = self.get_documento_formatado()
        nome = self.get_nome_completo()
        if documento:
            return f"{nome} ({documento})"
        return nome or self.username
    
    def pode_acessar_schema(self, schema_name):
        """
        Verifica se o usuário pode acessar um determinado schema.
        """
        return self.schema_name == schema_name or self.is_superuser

# Obtém o modelo de usuário configurado
User = get_user_model()


class TenantManager(models.Manager):
    """
    Manager customizado para filtrar automaticamente por tenant_id.
    Garante que cada usuário veja apenas seus próprios dados.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Verificar se há um tenant_id definido na conexão
        if hasattr(connection, 'tenant_id') and connection.tenant_id:
            queryset = queryset.filter(tenant_id=connection.tenant_id)
        
        return queryset
    
    def create(self, **kwargs):
        # Automaticamente definir o tenant_id ao criar novos objetos
        if hasattr(connection, 'tenant_id') and connection.tenant_id:
            kwargs['tenant_id'] = connection.tenant_id
        return super().create(**kwargs)
    
    def bulk_create(self, objs, **kwargs):
        # Definir tenant_id para criação em lote
        if hasattr(connection, 'tenant_id') and connection.tenant_id:
            for obj in objs:
                if not hasattr(obj, 'tenant_id') or obj.tenant_id is None:
                    obj.tenant_id = connection.tenant_id
        return super().bulk_create(objs, **kwargs)

class Tenant(models.Model):
    """
    Modelo para representar um tenant (inquilino) no sistema multi-tenant.
    Cada tenant representa uma organização ou usuário independente.
    """
    nome = models.CharField(max_length=100, help_text="Nome da organização ou usuário")
    codigo = models.CharField(max_length=20, unique=True, help_text="Código único do tenant")
    ativo = models.BooleanField(default=True, help_text="Se o tenant está ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    # Relacionamento com usuários do Django
    usuarios = models.ManyToManyField(User, related_name='tenants', blank=True)
    
    class Meta:
        ordering = ['nome']
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def clean(self):
        if not self.nome or not self.nome.strip():
            raise ValidationError({'nome': 'Nome é obrigatório'})
        if not self.codigo or not self.codigo.strip():
            raise ValidationError({'codigo': 'Código é obrigatório'})

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
        ('ambos', 'Ambos'),
    ]
    
    nome = models.CharField(max_length=100, unique=True)
    cor = models.CharField(max_length=20, default='#6c757d')  # Cor padrão cinza
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='ambos')
    tenant_id = models.IntegerField(null=True, blank=True, help_text="ID do tenant (usuário) para isolamento de dados")
    
    objects = TenantManager()
    
    class Meta:
        ordering = ['nome']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        import re
        
        errors = {}
        
        # Validação do nome
        if not self.nome or not self.nome.strip():
            errors['nome'] = 'Nome é obrigatório'
        elif len(self.nome.strip()) < 2:
            errors['nome'] = 'Nome deve ter pelo menos 2 caracteres'
        elif len(self.nome) > 50:
            errors['nome'] = 'Nome deve ter no máximo 50 caracteres'
        
        # Validação da cor (formato hexadecimal)
        if self.cor and not re.match(r'^#[0-9A-Fa-f]{6}$', self.cor):
            errors['cor'] = 'Cor deve estar no formato hexadecimal (#RRGGBB)'
        
        if errors:
            raise ValidationError(errors)
    
    def __str__(self):
        return self.nome

class Transacao(models.Model):
    data = models.DateField(default=timezone.now)
    descricao = models.CharField(
        max_length=ValidationConfig.MAX_DESCRICAO_LENGTH,
        help_text=f"Máximo {ValidationConfig.MAX_DESCRICAO_LENGTH} caracteres"
    )
    valor = models.DecimalField(
        max_digits=FormatConfig.MAX_DIGITS,
        decimal_places=FormatConfig.DECIMAL_PLACES
    )
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    tipo = models.CharField(
        max_length=10,
        choices=TipoTransacao.CHOICES
    )
    responsavel = models.CharField(max_length=100, blank=True, null=True)
    eh_parcelada = models.BooleanField(default=False)
    transacao_pai = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parcelas'
    )
    numero_parcela = models.IntegerField(null=True, blank=True)
    total_parcelas = models.IntegerField(null=True, blank=True)
    conta = models.ForeignKey('Conta', on_delete=models.CASCADE)
    despesa_parcelada = models.ForeignKey('DespesaParcelada', on_delete=models.CASCADE, null=True, blank=True)
    pago = models.BooleanField(default=False, help_text="Indica se a parcela foi paga")
    data_pagamento = models.DateField(null=True, blank=True, help_text="Data em que a parcela foi paga")
    tenant_id = models.IntegerField(null=True, blank=True, help_text="ID do tenant (usuário) para isolamento de dados")
    
    objects = TenantManager()
    
    def clean(self):
        """
        Validações customizadas para o modelo Transacao - Simplificadas.
        """
        # Validações removidas para permitir lançamento livre de transações
        pass
    
    def save(self, *args, **kwargs):
        """
        Override do save simplificado - sem validações restritivas.
        """
        # Removido full_clean() para permitir lançamento livre
        super().save(*args, **kwargs)
    
    def marcar_como_pago(self, data_pagamento=None):
        """Marca a parcela como paga"""
        self.pago = True
        self.data_pagamento = data_pagamento or timezone.now().date()
        self.save()
    
    def marcar_como_nao_pago(self):
        """Marca a parcela como não paga"""
        self.pago = False
        self.data_pagamento = None
        self.save()
    
    def __str__(self):
        if self.eh_parcelada and self.numero_parcela:
            status = " (PAGO)" if self.pago else " (PENDENTE)"
            return f"{self.descricao} - Parcela {self.numero_parcela}/{self.total_parcelas} - {FormatConfig.CURRENCY_SYMBOL} {self.valor}{status}"
        return f"{self.descricao} - {FormatConfig.CURRENCY_SYMBOL} {self.valor}"
    
    class Meta:
        ordering = ['-data']
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'

class DespesaParcelada(models.Model):
    INTERVALO_CHOICES = [
        ('mensal', 'Mensal'),
        ('quinzenal', 'Quinzenal'),
        ('semanal', 'Semanal'),
        ('personalizado', 'Personalizado (dias)'),
    ]
    
    descricao = models.CharField(max_length=200)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    responsavel = models.CharField(max_length=100, blank=True, null=True)
    numero_parcelas = models.IntegerField()
    data_primeira_parcela = models.DateField()
    dia_vencimento = models.IntegerField(default=1, help_text="Dia do mês para vencimento (1-31)")
    intervalo_tipo = models.CharField(max_length=15, choices=INTERVALO_CHOICES, default='mensal')
    intervalo_dias = models.IntegerField(null=True, blank=True, help_text="Número de dias para intervalo personalizado")
    criada_em = models.DateTimeField(default=timezone.now)
    parcelas_geradas = models.BooleanField(default=False)
    conta = models.ForeignKey('Conta', on_delete=models.CASCADE, default=1)
    tenant_id = models.IntegerField(null=True, blank=True, help_text="ID do tenant (usuário) para isolamento de dados")
    
    objects = TenantManager()
    
    def __str__(self):
        return f"{self.descricao} - {self.numero_parcelas}x de {self.valor_total/self.numero_parcelas}"
    
    @property
    def valor_parcela(self):
        return self.valor_total / self.numero_parcelas
    
    def get_parcelas(self):
        """Retorna as parcelas planejadas desta despesa parcelada"""
        return self.parcelas_planejadas.all().order_by('numero_parcela')
    
    def get_parcelas_pagas(self):
        """Retorna as parcelas pagas desta despesa parcelada"""
        return self.parcelas_planejadas.filter(pago=True).order_by('numero_parcela')
    
    def get_parcelas_pendentes(self):
        """Retorna as parcelas pendentes desta despesa parcelada"""
        return self.parcelas_planejadas.filter(pago=False).order_by('numero_parcela')
    
    def get_valor_pago(self):
        """Retorna o valor total pago das parcelas"""
        return sum(parcela.valor for parcela in self.get_parcelas_pagas())
    
    def get_valor_pendente(self):
        """Retorna o valor total pendente das parcelas"""
        return sum(parcela.valor for parcela in self.get_parcelas_pendentes())
    
    def excluir_com_parcelas(self):
        """Exclui a despesa parcelada e todas as suas parcelas"""
        # Excluir todas as parcelas planejadas (e suas transações se existirem)
        for parcela in self.parcelas_planejadas.all():
            if parcela.transacao_pagamento:
                parcela.transacao_pagamento.delete()
        self.parcelas_planejadas.all().delete()
        # Excluir a despesa parcelada
        self.delete()
    
    def gerar_parcelas(self):
        """Gera as parcelas planejadas da despesa parcelada (sem criar transações)"""
        if self.parcelas_geradas:
            return
        
        valor_parcela = self.valor_total / self.numero_parcelas
        data_vencimento = self.data_primeira_parcela
        
        for i in range(1, self.numero_parcelas + 1):
            # Ajusta o dia do vencimento se necessário
            if self.dia_vencimento > 1:
                data_vencimento = data_vencimento.replace(day=min(self.dia_vencimento, 28))
            
            # Criar parcela planejada (sem transação)
            ParcelaPlanejada.objects.create(
                despesa_parcelada=self,
                numero_parcela=i,
                data_vencimento=data_vencimento,
                valor=valor_parcela
            )
            
            # Calcula próxima data de vencimento
            if self.intervalo_tipo == 'mensal':
                data_vencimento = data_vencimento + relativedelta(months=1)
            elif self.intervalo_tipo == 'quinzenal':
                data_vencimento = data_vencimento + relativedelta(days=15)
            elif self.intervalo_tipo == 'semanal':
                data_vencimento = data_vencimento + relativedelta(days=7)
            elif self.intervalo_tipo == 'personalizado' and self.intervalo_dias:
                data_vencimento = data_vencimento + relativedelta(days=self.intervalo_dias)
        
        self.parcelas_geradas = True
        self.save()
    
    class Meta:
        ordering = ['-criada_em']

class Meta(models.Model):
    nome = models.CharField(max_length=100)
    valor_alvo = models.DecimalField(max_digits=10, decimal_places=2)
    data_limite = models.DateField()
    concluida = models.BooleanField(default=False)
    
    def __str__(self):
        return self.nome

class Banco(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    imagem = models.CharField(max_length=200, blank=True, null=True)  # URL da imagem
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Conta(models.Model):
    TIPO_CHOICES = [
        ('simples', 'Conta Simples'),
        ('bancaria', 'Conta Bancária'),
    ]
    
    nome = models.CharField(
        max_length=ValidationConfig.MAX_NOME_CONTA_LENGTH,
        help_text=f"Máximo {ValidationConfig.MAX_NOME_CONTA_LENGTH} caracteres"
    )
    saldo = models.DecimalField(
        max_digits=FormatConfig.MAX_DIGITS,
        decimal_places=FormatConfig.DECIMAL_PLACES,
        default=Decimal('0.00')
    )
    cor = models.CharField(max_length=7, default='#007bff', help_text="Cor da conta em formato hexadecimal")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='simples')
    
    # Campos específicos para conta bancária
    banco = models.ForeignKey(Banco, on_delete=models.SET_NULL, null=True, blank=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    numero_conta = models.CharField(max_length=20, blank=True, null=True)
    agencia = models.CharField(max_length=10, blank=True, null=True)
    tenant_id = models.IntegerField(null=True, blank=True, help_text="ID do tenant (usuário) para isolamento de dados")
    
    objects = TenantManager()
    
    def clean(self):
        """
        Validações customizadas para o modelo Conta - Simplificadas.
        """
        # Validações removidas para permitir lançamento livre
        pass
    
    def save(self, *args, **kwargs):
        """
        Override do save simplificado - sem validações restritivas.
        """
        # Removido full_clean() para permitir lançamento livre
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nome
    
    def is_conta_bancaria(self):
        return self.tipo == 'bancaria'
    
    def atualizar_saldo(self):
        """
        Atualiza o saldo da conta baseado nas transações após o último fechamento mensal.
        Se não houver fechamento, considera todas as transações.
        
        Returns:
            Decimal: O novo saldo da conta
        """
        from django.db.models import Sum
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Buscar último fechamento mensal
            ultimo_fechamento = self.fechamentomensal_set.filter(
                fechado=True
            ).order_by('-ano', '-mes').first()
            
            if ultimo_fechamento:
                # Se há fechamento, usar saldo final do fechamento como base
                saldo_base = ultimo_fechamento.saldo_final
                
                # Considerar apenas transações após o fechamento
                data_limite = ultimo_fechamento.data_fim_periodo or ultimo_fechamento.criado_em.date()
                transacoes_query = self.transacao_set.filter(data__gt=data_limite)
            else:
                # Se não há fechamento, considerar todas as transações
                saldo_base = Decimal('0.00')
                transacoes_query = self.transacao_set.all()
            
            # Calcular receitas após fechamento (todas as transações, independente do status pago)
            receitas = transacoes_query.filter(
                tipo=TipoTransacao.RECEITA
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            # Calcular despesas após fechamento (todas as transações, independente do status pago)
            despesas = transacoes_query.filter(
                tipo=TipoTransacao.DESPESA
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            # Calcular novo saldo
            novo_saldo = saldo_base + receitas - despesas
            saldo_anterior = self.saldo
            
            # Atualizar saldo (usando update para evitar recursão com signals)
            Conta.objects.filter(id=self.id).update(saldo=novo_saldo)
            self.saldo = novo_saldo
            
            logger.info(
                f"Saldo atualizado - Conta: {self.nome} - "
                f"Saldo anterior: {FormatConfig.CURRENCY_SYMBOL} {saldo_anterior} - "
                f"Novo saldo: {FormatConfig.CURRENCY_SYMBOL} {novo_saldo} - "
                f"Receitas: {FormatConfig.CURRENCY_SYMBOL} {receitas} - "
                f"Despesas: {FormatConfig.CURRENCY_SYMBOL} {despesas}"
            )
            
            return self.saldo
            
        except Exception as e:
            logger.error(f"Erro ao atualizar saldo da conta {self.nome}: {str(e)}")
            raise CustomValidationError(f"Erro ao atualizar saldo: {str(e)}")

class FechamentoMensal(models.Model):
    ano = models.IntegerField()
    mes = models.IntegerField()
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_receitas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_despesas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fechado = models.BooleanField(default=False)
    eh_parcial = models.BooleanField(default=False, help_text="Indica se foi fechamento antes do fim do mês")
    data_inicio_periodo = models.DateField(null=True, blank=True, help_text="Data de início do período considerado")
    data_fim_periodo = models.DateField(null=True, blank=True, help_text="Data de fim do período considerado")
    data_fechamento = models.DateTimeField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = [('conta', 'ano', 'mes')]
        ordering = ['-ano', '-mes']
    
    def __str__(self):
        meses = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return f"Fechamento {meses[self.mes]} {self.ano} - {self.conta.nome}"

class ConfiguracaoFechamento(models.Model):
    """
    Modelo para configurações de fechamento mensal.
    """
    # Configurações de fechamento automático
    fechamento_automatico_ativo = models.BooleanField(
        default=False,
        help_text="Ativa o fechamento automático no primeiro dia do mês"
    )
    
    # Configurações de restrições
    permitir_fechamento_apenas_mes_anterior = models.BooleanField(
        default=True,
        help_text="Permite fechamento apenas do mês anterior no dia 1"
    )
    
    # Configurações de notificação
    notificar_fechamento_automatico = models.BooleanField(
        default=True,
        help_text="Envia notificação quando fechamento automático é executado"
    )
    
    # Configurações de período de graça
    dias_graca_fechamento = models.IntegerField(
        default=0,
        help_text="Dias de graça após o dia 1 para permitir fechamento do mês anterior"
    )
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração de Fechamento"
        verbose_name_plural = "Configurações de Fechamento"
    
    def __str__(self):
        return f"Configuração de Fechamento - Automático: {'Sim' if self.fechamento_automatico_ativo else 'Não'}"
    
    @classmethod
    def get_configuracao(cls):
        """
        Retorna a configuração ativa ou cria uma padrão se não existir.
        """
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'fechamento_automatico_ativo': False,
                'permitir_fechamento_apenas_mes_anterior': True,
                'notificar_fechamento_automatico': True,
                'dias_graca_fechamento': 0,
            }
        )
        return config
    
    def pode_fechar_mes(self, ano, mes):
        """
        Verifica se é permitido fechar um determinado mês baseado nas configurações.
        
        Args:
            ano (int): Ano do fechamento
            mes (int): Mês do fechamento
            
        Returns:
            tuple: (pode_fechar: bool, motivo: str)
        """
        from datetime import date
        
        hoje = date.today()
        
        # Se não há restrição, permite qualquer fechamento
        if not self.permitir_fechamento_apenas_mes_anterior:
            return True, "Fechamento permitido"
        
        # Calcular mês anterior
        if hoje.month == 1:  # Janeiro
            mes_anterior = 12
            ano_anterior = hoje.year - 1
        else:
            mes_anterior = hoje.month - 1
            ano_anterior = hoje.year
        
        # Verifica se está tentando fechar o mês anterior (permitido durante todo o mês atual)
        if ano == ano_anterior and mes == mes_anterior:
            return True, "Fechamento do mês anterior permitido"
        
        # Verifica se está tentando fechar o mês atual (só permitido nos primeiros dias)
        if ano == hoje.year and mes == hoje.month:
            if hoje.day <= (1 + self.dias_graca_fechamento):
                return True, "Fechamento do mês atual permitido nos primeiros dias"
            else:
                return False, f"Fechamento do mês atual só é permitido até o dia {1 + self.dias_graca_fechamento}"
        
        # Qualquer outro caso não é permitido
        return False, "Só é permitido fechar o mês anterior ou o mês atual nos primeiros dias"


class ParcelaPlanejada(models.Model):
    """
    Representa uma parcela planejada de uma despesa parcelada.
    Não cria transação automaticamente - apenas quando confirmado o pagamento.
    """
    despesa_parcelada = models.ForeignKey('DespesaParcelada', on_delete=models.CASCADE, related_name='parcelas_planejadas')
    numero_parcela = models.IntegerField()
    data_vencimento = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)
    transacao_pagamento = models.ForeignKey('Transacao', on_delete=models.SET_NULL, null=True, blank=True, help_text="Transação criada quando a parcela foi paga")
    tenant_id = models.IntegerField(null=True, blank=True, help_text="ID do tenant (usuário) para isolamento de dados")
    
    objects = TenantManager()
    
    class Meta:
        ordering = ['numero_parcela']
        unique_together = [('despesa_parcelada', 'numero_parcela')]
        verbose_name = 'Parcela Planejada'
        verbose_name_plural = 'Parcelas Planejadas'
    
    def __str__(self):
        return f"{self.despesa_parcelada.descricao} - Parcela {self.numero_parcela}/{self.despesa_parcelada.numero_parcelas}"
    
    @property
    def descricao(self):
        """Retorna a descrição da parcela"""
        return f"{self.despesa_parcelada.descricao} - Parcela {self.numero_parcela}/{self.despesa_parcelada.numero_parcelas}"
    
    @property
    def categoria(self):
        """Retorna a categoria da despesa parcelada"""
        return self.despesa_parcelada.categoria
    
    @property
    def conta(self):
        """Retorna a conta da despesa parcelada"""
        return self.despesa_parcelada.conta
    
    @property
    def responsavel(self):
        """Retorna o responsável da despesa parcelada"""
        return self.despesa_parcelada.responsavel
    
    @property
    def total_parcelas(self):
        """Retorna o total de parcelas da despesa"""
        return self.despesa_parcelada.numero_parcelas
    
    def marcar_como_pago(self, data_pagamento, valor_pago=None):
        """
        Marca a parcela como paga e cria a transação correspondente.
        """
        if valor_pago is None:
            valor_pago = self.valor
            
        # Criar transação de pagamento
        transacao = Transacao.objects.create(
            data=data_pagamento,
            descricao=f"Pagamento: {self.descricao}",
            valor=valor_pago,
            categoria=self.categoria,
            tipo='despesa',
            responsavel=self.responsavel,
            eh_parcelada=False,
            conta=self.conta,
            pago=True,
            data_pagamento=data_pagamento
        )
        
        # Atualizar parcela
        self.pago = True
        self.data_pagamento = data_pagamento
        self.transacao_pagamento = transacao
        self.save()
        
        # Atualizar saldo da conta
        self.conta.atualizar_saldo()
        
        return transacao
    
    def marcar_como_nao_pago(self):
        """
        Marca a parcela como não paga e remove a transação correspondente.
        """
        if self.transacao_pagamento:
            self.transacao_pagamento.delete()
        
        self.pago = False
        self.data_pagamento = None
        self.transacao_pagamento = None
        self.save()
        
        # Atualizar saldo da conta
        self.conta.atualizar_saldo()


class PasswordResetToken(models.Model):
    """
    Modelo para tokens de reset de senha.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuário'
    )
    token = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Token'
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    usado = models.BooleanField(
        default=False,
        verbose_name='Usado'
    )
    expira_em = models.DateTimeField(
        verbose_name='Expira em'
    )
    
    class Meta:
        verbose_name = 'Token de Reset de Senha'
        verbose_name_plural = 'Tokens de Reset de Senha'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Token para {self.user.username} - {'Usado' if self.usado else 'Ativo'}"
    
    def is_valid(self):
        """
        Verifica se o token ainda é válido.
        """
        from django.utils import timezone
        return not self.usado and timezone.now() < self.expira_em
    
    def marcar_como_usado(self):
        """
        Marca o token como usado.
        """
        self.usado = True
        self.save()

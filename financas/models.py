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
                cpf_limpo = re.sub(r'\D', '', self.cpf)
                self.schema_name = f"user_{cpf_limpo}"
            elif self.tipo_pessoa == 'juridica' and self.cnpj:
                cnpj_limpo = re.sub(r'\D', '', self.cnpj)
                self.schema_name = f"user_{cnpj_limpo}"
        
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
    
    nome = models.CharField(max_length=100, db_index=True)  # Apenas índice, sem unique
    cor = models.CharField(max_length=20, default='#6c757d')  # Cor padrão cinza
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='ambos')
    tenant_id = models.IntegerField(null=True, blank=True, help_text="ID do tenant (usuário) para isolamento de dados", db_index=True)  # Adicionado índice
    
    objects = TenantManager()
    
    class Meta:
        ordering = ['nome']
        # Sem unique_together ou constraints
    
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
            
            # Calcula próxima data de vencimento (apenas se não for a última parcela)
            if i < self.numero_parcelas:
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
        Atualiza o saldo da conta baseado em todas as transações.
        
        Returns:
            Decimal: O novo saldo da conta
        """
        from django.db.models import Sum
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Considerar todas as transações
            saldo_base = Decimal('0.00')
            transacoes_query = self.transacao_set.all()
            
            # Calcular receitas (todas as transações, independente do status pago)
            receitas = transacoes_query.filter(
                tipo=TipoTransacao.RECEITA
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            # Calcular despesas (todas as transações, independente do status pago)
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

# Modelo para armazenar o fechamento mensal automático
class FechamentoMensal(models.Model):
    """
    Modelo para armazenar o fechamento mensal automático.
    Registra o saldo final de cada mês para cada conta.
    """
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE)
    mes = models.IntegerField(help_text="Mês do fechamento (1-12)")
    ano = models.IntegerField(help_text="Ano do fechamento")
    saldo_inicial = models.DecimalField(
        max_digits=FormatConfig.MAX_DIGITS,
        decimal_places=FormatConfig.DECIMAL_PLACES,
        default=Decimal('0.00'),
        help_text="Saldo inicial do mês"
    )
    total_receitas = models.DecimalField(
        max_digits=FormatConfig.MAX_DIGITS,
        decimal_places=FormatConfig.DECIMAL_PLACES,
        default=Decimal('0.00'),
        help_text="Total de receitas no mês"
    )
    total_despesas = models.DecimalField(
        max_digits=FormatConfig.MAX_DIGITS,
        decimal_places=FormatConfig.DECIMAL_PLACES,
        default=Decimal('0.00'),
        help_text="Total de despesas no mês"
    )
    saldo_final = models.DecimalField(
        max_digits=FormatConfig.MAX_DIGITS,
        decimal_places=FormatConfig.DECIMAL_PLACES,
        default=Decimal('0.00'),
        help_text="Saldo final do mês"
    )
    data_inicio_periodo = models.DateField(null=True, blank=True, help_text="Data de início do período")
    data_fim_periodo = models.DateField(null=True, blank=True, help_text="Data de fim do período")
    data_fechamento = models.DateTimeField(null=True, blank=True, help_text="Data e hora do fechamento")
    fechado = models.BooleanField(default=True, help_text="Indica se o mês está fechado")
    tenant_id = models.IntegerField(null=True, blank=True, help_text="ID do tenant (usuário) para isolamento de dados", db_index=True)
    
    objects = TenantManager()
    
    class Meta:
        ordering = ['ano', 'mes', 'conta']
        unique_together = [('conta', 'mes', 'ano')]
        verbose_name = 'Fechamento Mensal'
        verbose_name_plural = 'Fechamentos Mensais'
    
    def __str__(self):
        return f"{self.conta.nome} - {self.mes}/{self.ano} - Saldo: {FormatConfig.CURRENCY_SYMBOL} {self.saldo_final}"
    
    @classmethod
    def realizar_fechamento_automatico(cls):
        """
        Realiza o fechamento automático para todas as contas.
        Deve ser chamado no dia 1 de cada mês.
        """
        from django.db.models import Sum
        import logging
        
        logger = logging.getLogger(__name__)
        hoje = timezone.now().date()
        
        # Verificar se é dia 1 do mês
        if hoje.day != 1:
            logger.info(f"Fechamento automático não executado - Hoje não é dia 1 (é dia {hoje.day})")
            return False, "Fechamento automático só pode ser executado no dia 1 do mês."
        
        # Determinar mês e ano para fechamento (mês anterior)
        if hoje.month == 1:
            mes_fechamento = 12
            ano_fechamento = hoje.year - 1
        else:
            mes_fechamento = hoje.month - 1
            ano_fechamento = hoje.year
        
        # Calcular período de fechamento
        data_inicio = date(ano_fechamento, mes_fechamento, 1)
        if mes_fechamento == 12:
            data_fim = date(ano_fechamento + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(ano_fechamento, mes_fechamento + 1, 1) - timedelta(days=1)
        
        # Processar cada conta
        contas = Conta.objects.all()
        fechamentos_realizados = []
        
        for conta in contas:
            # Verificar se já existe fechamento para esta conta/mês/ano
            if cls.objects.filter(conta=conta, mes=mes_fechamento, ano=ano_fechamento).exists():
                logger.info(f"Fechamento já existe para {conta.nome} - {mes_fechamento}/{ano_fechamento}")
                continue
            
            # Buscar transações do período
            transacoes = Transacao.objects.filter(
                conta=conta,
                data__gte=data_inicio,
                data__lte=data_fim
            )
            
            # Calcular receitas e despesas
            receitas = transacoes.filter(tipo=TipoTransacao.RECEITA).aggregate(
                total=Sum('valor'))['total'] or Decimal('0.00')
            despesas = transacoes.filter(tipo=TipoTransacao.DESPESA).aggregate(
                total=Sum('valor'))['total'] or Decimal('0.00')
            
            # Buscar fechamento anterior para saldo inicial
            fechamento_anterior = cls.objects.filter(
                conta=conta
            ).filter(
                models.Q(ano__lt=ano_fechamento) | 
                models.Q(ano=ano_fechamento, mes__lt=mes_fechamento)
            ).order_by('-ano', '-mes').first()
            
            saldo_inicial = fechamento_anterior.saldo_final if fechamento_anterior else Decimal('0.00')
            saldo_final = saldo_inicial + receitas - despesas
            
            # Criar fechamento
            fechamento = cls.objects.create(
                conta=conta,
                mes=mes_fechamento,
                ano=ano_fechamento,
                saldo_inicial=saldo_inicial,
                total_receitas=receitas,
                total_despesas=despesas,
                saldo_final=saldo_final,
                data_inicio_periodo=data_inicio,
                data_fim_periodo=data_fim,
                data_fechamento=timezone.now(),
                fechado=True
            )
            
            fechamentos_realizados.append(fechamento)
            logger.info(f"Fechamento automático realizado: {conta.nome} - {mes_fechamento}/{ano_fechamento}")
        
        return True, fechamentos_realizados

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

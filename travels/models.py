from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class UserProfile(models.Model):
    """Perfil do usuário estendendo o modelo User do Django"""
    USER_TYPE_CHOICES = [
        ('SOLICITANTE', 'Solicitante'),
        ('APROVADOR', 'Aprovador'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES, default='SOLICITANTE')
    cpf = models.CharField(max_length=14, blank=True, null=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_user_type_display()}"

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"


class BankAccount(models.Model):
    """Dados bancários do usuário para reembolso"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_account')
    banco = models.CharField(max_length=100, help_text="Nome do banco")
    codigo_banco = models.CharField(max_length=10, help_text="Código do banco (ex: 001, 237)")
    agencia = models.CharField(max_length=10, help_text="Número da agência")
    conta = models.CharField(max_length=20, help_text="Número da conta com dígito")
    tipo_conta = models.CharField(
        max_length=20,
        choices=[('CORRENTE', 'Conta Corrente'), ('POUPANCA', 'Conta Poupança')],
        default='CORRENTE'
    )
    titular = models.CharField(max_length=200, help_text="Nome do titular da conta")
    cpf_titular = models.CharField(max_length=14, help_text="CPF do titular")

    def __str__(self):
        return f"{self.banco} - Ag: {self.agencia} Conta: {self.conta}"

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"


class TravelRequest(models.Model):
    """Solicitação de viagem"""
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('REJEITADA', 'Rejeitada'),
    ]

    # Dados da viagem
    solicitante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='travel_requests',
        verbose_name="Solicitante"
    )
    destino = models.CharField(max_length=200, verbose_name="Destino")
    data_viagem = models.DateField(verbose_name="Data da Viagem")
    quilometragem = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Quilometragem rodada (km)"
    )

    # Dados de combustível
    valor_litro = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Valor do litro da gasolina (R$)",
        null=True,
        blank=True
    )
    valor_total_combustivel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Valor total gasto com combustível (R$)"
    )

    # Documentação
    nota_fiscal = models.FileField(
        upload_to='notas_fiscais/%Y/%m/',
        verbose_name="Nota Fiscal",
        help_text="Upload da nota fiscal de combustível"
    )

    # Dados bancários (referência)
    conta_bancaria = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Conta para Reembolso"
    )

    # Controle de aprovação
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name="Status"
    )
    aprovador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_travels',
        verbose_name="Aprovador"
    )
    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Aprovação/Rejeição"
    )
    observacoes_aprovador = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações do Aprovador"
    )

    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    def __str__(self):
        return f"{self.destino} - {self.solicitante.get_full_name() or self.solicitante.username} - {self.get_status_display()}"

    def calcular_gasto_total(self):
        """Calcula o valor total do gasto (já informado pelo usuário)"""
        return self.valor_total_combustivel

    class Meta:
        verbose_name = "Solicitação de Viagem"
        verbose_name_plural = "Solicitações de Viagem"
        ordering = ['-data_criacao']


# Signal para criar UserProfile automaticamente quando criar um User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

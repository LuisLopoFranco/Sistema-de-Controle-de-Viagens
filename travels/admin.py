from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import AdminPasswordChangeForm
from .models import UserProfile, BankAccount, TravelRequest, SystemConfig


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__user_type')
    actions = ['ativar_usuarios', 'inativar_usuarios', 'tornar_aprovador', 'tornar_solicitante']

    def get_user_type(self, obj):
        return obj.profile.get_user_type_display() if hasattr(obj, 'profile') else '-'
    get_user_type.short_description = 'Tipo de Usuário'

    def ativar_usuarios(self, request, queryset):
        """Ativar usuários selecionados"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} usuário(s) ativado(s) com sucesso.',
            messages.SUCCESS
        )
    ativar_usuarios.short_description = "Ativar usuários selecionados"

    def inativar_usuarios(self, request, queryset):
        """Inativar usuários selecionados"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} usuário(s) inativado(s) com sucesso.',
            messages.SUCCESS
        )
    inativar_usuarios.short_description = "Inativar usuários selecionados"

    def tornar_aprovador(self, request, queryset):
        """Tornar usuários aprovadores"""
        count = 0
        for user in queryset:
            if hasattr(user, 'profile'):
                user.profile.user_type = 'APROVADOR'
                user.profile.save()
                count += 1
        self.message_user(
            request,
            f'{count} usuário(s) alterado(s) para Aprovador.',
            messages.SUCCESS
        )
    tornar_aprovador.short_description = "Tornar usuários APROVADORES"

    def tornar_solicitante(self, request, queryset):
        """Tornar usuários solicitantes"""
        count = 0
        for user in queryset:
            if hasattr(user, 'profile'):
                user.profile.user_type = 'SOLICITANTE'
                user.profile.save()
                count += 1
        self.message_user(
            request,
            f'{count} usuário(s) alterado(s) para Solicitante.',
            messages.SUCCESS
        )
    tornar_solicitante.short_description = "Tornar usuários SOLICITANTES"


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'banco', 'agencia', 'conta', 'tipo_conta')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'banco', 'titular')
    list_filter = ('tipo_conta', 'banco')


@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    list_display = (
        'destino',
        'solicitante',
        'data_viagem',
        'valor_total_combustivel',
        'status',
        'aprovador',
        'data_criacao'
    )
    list_filter = ('status', 'data_viagem', 'data_criacao')
    search_fields = (
        'destino',
        'solicitante__username',
        'solicitante__first_name',
        'solicitante__last_name'
    )
    readonly_fields = ('data_criacao', 'data_atualizacao')

    fieldsets = (
        ('Informações da Viagem', {
            'fields': (
                'solicitante',
                'destino',
                'data_viagem',
                'quilometragem',
                'valor_litro',
                'consumo_medio',
                'valor_total_combustivel',
                'nota_fiscal',
                'conta_bancaria'
            )
        }),
        ('Aprovação', {
            'fields': (
                'status',
                'aprovador',
                'data_aprovacao',
                'observacoes_aprovador'
            )
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # Se o status foi alterado, registrar quem aprovou
            if obj.status in ['APROVADA', 'REJEITADA'] and not obj.aprovador:
                obj.aprovador = request.user
                from django.utils import timezone
                obj.data_aprovacao = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'app_url', 'consumo_medio_padrao', 'empresa')
    fieldsets = (
        ('Informações da Aplicação', {
            'fields': ('app_name', 'app_url', 'empresa')
        }),
        ('Configurações de Cálculo', {
            'fields': ('consumo_medio_padrao',)
        }),
    )

    def has_add_permission(self, request):
        # Permitir adicionar apenas se não existe configuração
        return not SystemConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Não permitir exclusão
        return False

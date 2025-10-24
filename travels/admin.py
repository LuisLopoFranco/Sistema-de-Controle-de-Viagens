from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, BankAccount, TravelRequest


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__user_type')

    def get_user_type(self, obj):
        return obj.profile.get_user_type_display() if hasattr(obj, 'profile') else '-'
    get_user_type.short_description = 'Tipo de Usuário'


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

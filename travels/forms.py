from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TravelRequest, BankAccount, UserProfile


class UserRegistrationForm(UserCreationForm):
    """Formulário de registro de usuário"""
    email = forms.EmailField(required=True, label="E-mail")
    first_name = forms.CharField(required=True, label="Nome")
    last_name = forms.CharField(required=True, label="Sobrenome")
    cpf = forms.CharField(max_length=14, required=False, label="CPF")
    telefone = forms.CharField(max_length=15, required=False, label="Telefone")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Atualizar o profile que foi criado automaticamente pelo signal
            user.profile.cpf = self.cleaned_data.get('cpf', '')
            user.profile.telefone = self.cleaned_data.get('telefone', '')
            user.profile.save()

        return user


class BankAccountForm(forms.ModelForm):
    """Formulário de dados bancários"""
    class Meta:
        model = BankAccount
        fields = [
            'banco',
            'codigo_banco',
            'agencia',
            'conta',
            'tipo_conta',
            'titular',
            'cpf_titular'
        ]
        widgets = {
            'banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Banco do Brasil'}),
            'codigo_banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 001'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1234-5'}),
            'conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12345-6'}),
            'tipo_conta': forms.Select(attrs={'class': 'form-control'}),
            'titular': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf_titular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 123.456.789-00'}),
        }


class TravelRequestForm(forms.ModelForm):
    """Formulário de solicitação de viagem"""
    class Meta:
        model = TravelRequest
        fields = [
            'destino',
            'data_viagem',
            'quilometragem',
            'valor_litro',
            'valor_total_combustivel',
            'nota_fiscal',
            'conta_bancaria'
        ]
        widgets = {
            'destino': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: São Paulo - SP'
            }),
            'data_viagem': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'quilometragem': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 150.50',
                'step': '0.01'
            }),
            'valor_litro': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 5.50',
                'step': '0.01'
            }),
            'valor_total_combustivel': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 165.00',
                'step': '0.01'
            }),
            'nota_fiscal': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,application/pdf'
            }),
            'conta_bancaria': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrar contas bancárias apenas do usuário logado
        if user:
            self.fields['conta_bancaria'].queryset = BankAccount.objects.filter(user=user)

        # Tornar conta_bancaria obrigatória
        self.fields['conta_bancaria'].required = True
        self.fields['conta_bancaria'].empty_label = "Selecione uma conta bancária"


class TravelApprovalForm(forms.Form):
    """Formulário de aprovação/rejeição de viagem"""
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações sobre a aprovação/rejeição (opcional)'
        }),
        required=False,
        label="Observações"
    )

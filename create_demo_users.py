#!/usr/bin/env python
"""
Script para criar usuários de demonstração no sistema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_system.settings')
django.setup()

from django.contrib.auth.models import User
from travels.models import UserProfile, BankAccount

def create_demo_users():
    print("Criando usuários de demonstração...")

    # Criar superusuário (aprovador)
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        admin.profile.user_type = 'APROVADOR'
        admin.profile.save()
        print("✓ Superusuário criado: admin / admin123 (APROVADOR)")
    else:
        print("✓ Superusuário 'admin' já existe")

    # Criar aprovador
    if not User.objects.filter(username='aprovador').exists():
        aprovador = User.objects.create_user(
            username='aprovador',
            email='aprovador@example.com',
            password='aprovador123',
            first_name='João',
            last_name='Silva'
        )
        aprovador.profile.user_type = 'APROVADOR'
        aprovador.profile.cpf = '123.456.789-00'
        aprovador.profile.telefone = '(11) 98765-4321'
        aprovador.profile.save()
        print("✓ Aprovador criado: aprovador / aprovador123")
    else:
        print("✓ Aprovador 'aprovador' já existe")

    # Criar solicitante
    if not User.objects.filter(username='solicitante').exists():
        solicitante = User.objects.create_user(
            username='solicitante',
            email='solicitante@example.com',
            password='solicitante123',
            first_name='Maria',
            last_name='Santos'
        )
        solicitante.profile.user_type = 'SOLICITANTE'
        solicitante.profile.cpf = '987.654.321-00'
        solicitante.profile.telefone = '(11) 91234-5678'
        solicitante.profile.save()

        # Criar conta bancária para o solicitante
        BankAccount.objects.create(
            user=solicitante,
            banco='Banco do Brasil',
            codigo_banco='001',
            agencia='1234-5',
            conta='12345-6',
            tipo_conta='CORRENTE',
            titular='Maria Santos',
            cpf_titular='987.654.321-00'
        )
        print("✓ Solicitante criado: solicitante / solicitante123")
        print("  - Conta bancária cadastrada")
    else:
        print("✓ Solicitante 'solicitante' já existe")

    # Criar mais solicitantes para demonstração
    for i in range(1, 4):
        username = f'colaborador{i}'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=f'colaborador{i}@example.com',
                password=f'senha{i}23',
                first_name=f'Colaborador',
                last_name=f'{i}'
            )
            user.profile.user_type = 'SOLICITANTE'
            user.profile.save()

            BankAccount.objects.create(
                user=user,
                banco='Caixa Econômica Federal',
                codigo_banco='104',
                agencia=f'000{i}',
                conta=f'0000{i}-0',
                tipo_conta='CORRENTE',
                titular=f'Colaborador {i}',
                cpf_titular=f'111.222.333-{i:02d}'
            )
            print(f"✓ Colaborador{i} criado: {username} / senha{i}23")

    print("\n" + "="*60)
    print("USUÁRIOS DE DEMONSTRAÇÃO CRIADOS COM SUCESSO!")
    print("="*60)
    print("\nPara fazer login, use:")
    print("\n--- APROVADORES ---")
    print("Usuário: admin         | Senha: admin123")
    print("Usuário: aprovador     | Senha: aprovador123")
    print("\n--- SOLICITANTES ---")
    print("Usuário: solicitante   | Senha: solicitante123")
    print("Usuário: colaborador1  | Senha: senha123")
    print("Usuário: colaborador2  | Senha: senha223")
    print("Usuário: colaborador3  | Senha: senha323")
    print("="*60)

if __name__ == '__main__':
    create_demo_users()

"""
Cria usuários de demonstração com senhas geradas.

Substitui o create_demo_users.py, que trazia senhas fixas e fracas escritas
no próprio repositório ('admin123', 'senha123'). Isso é aceitável num
ambiente local descartável e péssimo em qualquer outro — e nada impedia que
o script fosse executado por engano num servidor.

Aqui as senhas são geradas na hora e impressas uma única vez. Não ficam no
código, não ficam no histórico do Git.
"""

import secrets
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from travels.models import BankAccount

ALFABETO = string.ascii_letters + string.digits
TAMANHO_SENHA = 16

USUARIOS_DEMO = [
    ("admin", "Administrador", "Sistema", "APROVADOR", True),
    ("aprovador", "Ana", "Ribeiro", "APROVADOR", False),
    ("solicitante", "João", "Silva", "SOLICITANTE", False),
]


class Command(BaseCommand):
    help = "Cria usuários de demonstração com senhas aleatórias."

    def add_arguments(self, parser):
        parser.add_argument(
            "--forcar",
            action="store_true",
            help="Permite rodar mesmo com DEBUG=False (use por sua conta e risco).",
        )

    @transaction.atomic
    def handle(self, *args, **opcoes):
        from django.conf import settings

        # Barreira contra o acidente: rodar isto em produção criaria contas
        # administrativas de demonstração num sistema real.
        if not settings.DEBUG and not opcoes["forcar"]:
            raise CommandError(
                "DEBUG=False: este comando cria contas de demonstração e não "
                "deve rodar em produção. Use --forcar se tiver certeza."
            )

        credenciais = []

        for username, nome, sobrenome, perfil, superusuario in USUARIOS_DEMO:
            if User.objects.filter(username=username).exists():
                self.stdout.write(f"  {username}: já existe, mantido como está")
                continue

            senha = self._gerar_senha()
            criar = User.objects.create_superuser if superusuario else User.objects.create_user
            usuario = criar(
                username=username,
                email=f"{username}@exemplo.local",
                password=senha,
                first_name=nome,
                last_name=sobrenome,
            )
            usuario.profile.user_type = perfil
            usuario.profile.save()

            if perfil == "SOLICITANTE":
                self._criar_conta_bancaria(usuario)

            credenciais.append((username, senha, perfil))
            self.stdout.write(self.style.SUCCESS(f"  {username}: criado ({perfil})"))

        self._imprimir_credenciais(credenciais)

    def _gerar_senha(self):
        return "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO_SENHA))

    def _criar_conta_bancaria(self, usuario):
        BankAccount.objects.create(
            user=usuario,
            banco="Banco Demonstração",
            codigo_banco="000",
            agencia="0001",
            conta="12345-6",
            tipo_conta="CORRENTE",
            titular=usuario.get_full_name(),
            cpf_titular="000.000.000-00",
        )

    def _imprimir_credenciais(self, credenciais):
        if not credenciais:
            self.stdout.write("\nNenhum usuário novo foi criado.")
            return

        self.stdout.write(self.style.WARNING("\n  Anote agora — não será exibido de novo:\n"))
        for username, senha, perfil in credenciais:
            self.stdout.write(f"    {username:<14} {senha}   ({perfil})")
        self.stdout.write("")

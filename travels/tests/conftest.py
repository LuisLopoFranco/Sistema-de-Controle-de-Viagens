"""
Fixtures compartilhadas pelos testes do app travels.

Tudo que mais de um arquivo de teste precisa mora aqui: usuários dos dois
perfis, conta bancária, arquivos de nota fiscal válidos e inválidos, e uma
fábrica de solicitações.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from travels.models import BankAccount, TravelRequest

# Conteúdo mínimo que passa na checagem de assinatura binária.
PDF_VALIDO = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
PNG_VALIDO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG_VALIDO = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture(autouse=True)
def sem_redirecionamento_https(settings):
    """
    Desliga o redirecionamento para HTTPS durante os testes.

    Os testes rodam com DEBUG=False para exercitar a configuração real de
    produção, e isso liga SECURE_SSL_REDIRECT. Só que o cliente de teste do
    Django fala HTTP: sem esta fixture, toda requisição responderia 301 antes
    de chegar na view e nenhum teste de permissão testaria coisa alguma.
    """
    settings.SECURE_SSL_REDIRECT = False


@pytest.fixture(autouse=True)
def media_temporaria(settings, tmp_path):
    """
    Redireciona os uploads para um diretório temporário.

    Sem isso, cada execução dos testes deixaria arquivos na pasta media/ do
    projeto. O autouse=True aplica a todos os testes automaticamente.
    """
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


@pytest.fixture
def solicitante(db):
    """Usuário comum. O perfil é criado pelo signal, já como SOLICITANTE."""
    return User.objects.create_user(
        username="joao",
        password="senha-de-teste-123",
        first_name="João",
        last_name="Silva",
    )


@pytest.fixture
def outro_solicitante(db):
    """Segundo solicitante, para testar isolamento entre usuários."""
    return User.objects.create_user(
        username="maria",
        password="senha-de-teste-123",
        first_name="Maria",
        last_name="Souza",
    )


@pytest.fixture
def aprovador(db):
    """Usuário com perfil de aprovador."""
    usuario = User.objects.create_user(
        username="carlos",
        password="senha-de-teste-123",
        first_name="Carlos",
        last_name="Lima",
    )
    usuario.profile.user_type = "APROVADOR"
    usuario.profile.save()
    return usuario


@pytest.fixture
def conta_bancaria(solicitante):
    return BankAccount.objects.create(
        user=solicitante,
        banco="Sicoob",
        codigo_banco="756",
        agencia="1234",
        conta="56789-0",
        tipo_conta="CORRENTE",
        titular="João Silva",
        cpf_titular="123.456.789-00",
    )


@pytest.fixture
def nota_pdf():
    """Arquivo de nota fiscal válido."""
    return SimpleUploadedFile("nota.pdf", PDF_VALIDO, content_type="application/pdf")


@pytest.fixture
def criar_solicitacao(solicitante, conta_bancaria):
    """
    Fábrica de solicitações. Recebe sobrescritas por keyword:

        criar_solicitacao(status="APROVADA", destino="Anápolis")
    """

    def _criar(**sobrescritas):
        dados = {
            "solicitante": solicitante,
            "destino": "Goiânia",
            "data_viagem": date.today() - timedelta(days=1),
            "quilometragem": Decimal("100.00"),
            "valor_litro": Decimal("5.50"),
            "consumo_medio": Decimal("10.00"),
            "conta_bancaria": conta_bancaria,
            "nota_fiscal": SimpleUploadedFile(
                "nota.pdf", PDF_VALIDO, content_type="application/pdf"
            ),
        }
        dados.update(sobrescritas)
        return TravelRequest.objects.create(**dados)

    return _criar

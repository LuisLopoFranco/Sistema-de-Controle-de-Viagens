"""
Testes de controle de acesso.

Duas perguntas em cada teste: quem pode ver, e quem não pode. A segunda é a
que importa — sistema que só é testado com o usuário certo passa despercebido
até alguém tentar o contrário.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# --------------------------------------------------------------------------
# Nota fiscal — o documento com dados pessoais
# --------------------------------------------------------------------------


def test_anonimo_nao_baixa_nota_fiscal(client, criar_solicitacao):
    """Antes da Fase 1, este arquivo era público para quem tivesse a URL."""
    solicitacao = criar_solicitacao()

    resposta = client.get(reverse("nota_fiscal", args=[solicitacao.pk]))

    assert resposta.status_code == 302
    assert "/login/" in resposta.url


def test_dono_baixa_a_propria_nota_fiscal(client, solicitante, criar_solicitacao):
    solicitacao = criar_solicitacao()
    client.force_login(solicitante)

    resposta = client.get(reverse("nota_fiscal", args=[solicitacao.pk]))

    assert resposta.status_code == 200


def test_aprovador_baixa_nota_de_qualquer_solicitacao(
    client, aprovador, criar_solicitacao
):
    solicitacao = criar_solicitacao()
    client.force_login(aprovador)

    resposta = client.get(reverse("nota_fiscal", args=[solicitacao.pk]))

    assert resposta.status_code == 200


def test_outro_solicitante_nao_baixa_nota_alheia(
    client, outro_solicitante, criar_solicitacao
):
    """
    404 em vez de 403 é proposital: 403 confirmaria que a solicitação existe,
    permitindo enumerar registros do sistema.
    """
    solicitacao = criar_solicitacao()
    client.force_login(outro_solicitante)

    resposta = client.get(reverse("nota_fiscal", args=[solicitacao.pk]))

    assert resposta.status_code == 404


def test_solicitacao_inexistente_retorna_404(client, aprovador):
    client.force_login(aprovador)

    resposta = client.get(reverse("nota_fiscal", args=[99999]))

    assert resposta.status_code == 404


# --------------------------------------------------------------------------
# Detalhe da solicitação
# --------------------------------------------------------------------------


def test_dono_ve_o_detalhe_da_propria_solicitacao(
    client, solicitante, criar_solicitacao
):
    solicitacao = criar_solicitacao()
    client.force_login(solicitante)

    resposta = client.get(reverse("request_detail", args=[solicitacao.pk]))

    assert resposta.status_code == 200


def test_outro_solicitante_e_redirecionado_no_detalhe(
    client, outro_solicitante, criar_solicitacao
):
    solicitacao = criar_solicitacao()
    client.force_login(outro_solicitante)

    resposta = client.get(reverse("request_detail", args=[solicitacao.pk]))

    assert resposta.status_code == 302
    assert resposta.url == reverse("home")


# --------------------------------------------------------------------------
# Telas restritas a aprovador
# --------------------------------------------------------------------------


@pytest.mark.parametrize("rota", ["dashboard", "all_requests"])
def test_solicitante_nao_acessa_telas_de_aprovador(client, solicitante, rota):
    client.force_login(solicitante)

    resposta = client.get(reverse(rota))

    assert resposta.status_code == 302


@pytest.mark.parametrize("rota", ["dashboard", "all_requests"])
def test_aprovador_acessa_telas_de_aprovador(client, aprovador, rota):
    client.force_login(aprovador)

    resposta = client.get(reverse(rota))

    assert resposta.status_code == 200


@pytest.mark.parametrize("rota", ["home", "my_requests", "create_request", "dashboard"])
def test_telas_internas_exigem_login(client, rota):
    resposta = client.get(reverse(rota))

    assert resposta.status_code == 302
    assert "/login/" in resposta.url

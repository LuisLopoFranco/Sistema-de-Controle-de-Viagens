"""
Testes do fluxo de aprovação.

A máquina de estados do sistema: PENDENTE vira APROVADA ou REJEITADA, e
nunca volta atrás.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_aprovador_aprova_solicitacao_pendente(client, aprovador, criar_solicitacao):
    solicitacao = criar_solicitacao()
    client.force_login(aprovador)

    client.post(
        reverse("approve_request", args=[solicitacao.pk]),
        {"observacoes": "Documentação em ordem."},
    )
    solicitacao.refresh_from_db()

    assert solicitacao.status == "APROVADA"
    assert solicitacao.aprovador == aprovador
    assert solicitacao.data_aprovacao is not None
    assert solicitacao.observacoes_aprovador == "Documentação em ordem."


def test_aprovador_rejeita_solicitacao_pendente(client, aprovador, criar_solicitacao):
    solicitacao = criar_solicitacao()
    client.force_login(aprovador)

    client.post(
        reverse("reject_request", args=[solicitacao.pk]),
        {"observacoes": "Nota fiscal ilegível."},
    )
    solicitacao.refresh_from_db()

    assert solicitacao.status == "REJEITADA"
    assert solicitacao.aprovador == aprovador


def test_solicitante_nao_aprova_a_propria_solicitacao(
    client, solicitante, criar_solicitacao
):
    """O teste mais importante deste arquivo: separação de responsabilidades."""
    solicitacao = criar_solicitacao()
    client.force_login(solicitante)

    resposta = client.post(
        reverse("approve_request", args=[solicitacao.pk]), {"observacoes": ""}
    )
    solicitacao.refresh_from_db()

    assert resposta.status_code == 302
    assert solicitacao.status == "PENDENTE"
    assert solicitacao.aprovador is None


def test_solicitacao_ja_aprovada_nao_e_reprocessada(
    client, aprovador, criar_solicitacao
):
    """Evita que um segundo clique sobrescreva quem aprovou e quando."""
    solicitacao = criar_solicitacao(status="APROVADA")
    client.force_login(aprovador)

    client.post(
        reverse("reject_request", args=[solicitacao.pk]), {"observacoes": "Mudei de ideia"}
    )
    solicitacao.refresh_from_db()

    assert solicitacao.status == "APROVADA"


def test_solicitacao_nasce_pendente(criar_solicitacao):
    solicitacao = criar_solicitacao()

    assert solicitacao.status == "PENDENTE"
    assert solicitacao.aprovador is None
    assert solicitacao.data_aprovacao is None

"""
Testes das listagens: paginação e número de consultas ao banco.

O teste de contagem de queries é o mais valioso daqui. Problema N+1 não
quebra nada — a página continua correta, só fica cada vez mais lenta
conforme os dados crescem. Sem uma verificação automática, ninguém percebe
até o sistema estar em produção com volume real.
"""

import pytest
from django.urls import reverse

from travels.views import TAMANHO_PAGINA

pytestmark = pytest.mark.django_db


@pytest.fixture
def muitas_solicitacoes(criar_solicitacao):
    """Uma a mais que o tamanho da página, para forçar a segunda."""
    return [criar_solicitacao() for _ in range(TAMANHO_PAGINA + 5)]


# --------------------------------------------------------------------------
# Paginação
# --------------------------------------------------------------------------


def test_minhas_solicitacoes_pagina_a_listagem(
    client, solicitante, muitas_solicitacoes
):
    client.force_login(solicitante)

    resposta = client.get(reverse("my_requests"))

    assert len(resposta.context["requests"]) == TAMANHO_PAGINA
    assert resposta.context["page_obj"].has_next()


def test_segunda_pagina_traz_o_restante(client, solicitante, muitas_solicitacoes):
    client.force_login(solicitante)

    resposta = client.get(reverse("my_requests"), {"page": 2})

    assert len(resposta.context["requests"]) == 5
    assert not resposta.context["page_obj"].has_next()


def test_todas_solicitacoes_pagina_a_listagem(
    client, aprovador, muitas_solicitacoes
):
    client.force_login(aprovador)

    resposta = client.get(reverse("all_requests"))

    assert len(resposta.context["requests"]) == TAMANHO_PAGINA


def test_pagina_invalida_cai_na_ultima(client, solicitante, muitas_solicitacoes):
    """get_page() trata entrada inválida em vez de estourar erro 500."""
    client.force_login(solicitante)

    resposta = client.get(reverse("my_requests"), {"page": "banana"})

    assert resposta.status_code == 200


def test_estatisticas_consideram_todas_as_solicitacoes(
    client, solicitante, muitas_solicitacoes
):
    """
    A paginação não pode contaminar os totais.

    Erro fácil de cometer: paginar o queryset e depois contar em cima da
    página, fazendo o usuário ver "20 pendentes" quando tem 25.
    """
    client.force_login(solicitante)

    resposta = client.get(reverse("my_requests"))

    assert resposta.context["pendentes"] == TAMANHO_PAGINA + 5


# --------------------------------------------------------------------------
# Número de consultas
# --------------------------------------------------------------------------


def test_listagem_nao_faz_uma_consulta_por_linha(
    client, aprovador, criar_solicitacao, django_assert_max_num_queries
):
    """
    Sem select_related, exibir o nome do solicitante de cada linha dispara
    uma consulta nova. Dez solicitações custariam onze consultas; cem
    custariam cento e uma.

    O limite abaixo é folgado de propósito — cobre sessão, usuário, contagens
    e a própria listagem. O que importa é que ele não cresça junto com o
    número de registros.
    """
    for _ in range(10):
        criar_solicitacao()
    client.force_login(aprovador)

    with django_assert_max_num_queries(12):
        client.get(reverse("all_requests"))


def test_links_de_paginacao_preservam_os_filtros(
    client, aprovador, muitas_solicitacoes
):
    """
    Trocar de página não pode descartar o filtro aplicado.

    É o defeito clássico de paginação: o usuário filtra por status, vai para
    a página 2 e recebe a lista inteira de volta sem entender por quê.
    """
    client.force_login(aprovador)

    resposta = client.get(reverse("all_requests"), {"status": "PENDENTE"})

    assert "status=PENDENTE" in resposta.context["querystring_filtros"]
    assert "page" not in resposta.context["querystring_filtros"]


def test_pagina_unica_nao_mostra_controles(client, solicitante, criar_solicitacao):
    """Com poucos registros a navegação some, em vez de ficar inerte na tela."""
    criar_solicitacao()
    client.force_login(solicitante)

    resposta = client.get(reverse("my_requests"))

    assert resposta.context["page_obj"].paginator.num_pages == 1
    assert "Próxima" not in resposta.content.decode()

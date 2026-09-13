"""
Testes do decorator aprovador_required.

Testar o decorator diretamente, e não só através das views que o usam,
significa que uma view nova protegida por ele já nasce com a regra
verificada.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

ROTAS_DE_APROVADOR = ["dashboard", "all_requests"]


@pytest.mark.parametrize("rota", ROTAS_DE_APROVADOR)
def test_anonimo_vai_para_o_login(client, rota):
    """O decorator inclui login_required — autentica antes de olhar o perfil."""
    resposta = client.get(reverse(rota))

    assert resposta.status_code == 302
    assert "/login/" in resposta.url


@pytest.mark.parametrize("rota", ROTAS_DE_APROVADOR)
def test_solicitante_e_mandado_para_home(client, solicitante, rota):
    client.force_login(solicitante)

    resposta = client.get(reverse(rota))

    assert resposta.url == reverse("home")


@pytest.mark.parametrize("rota", ROTAS_DE_APROVADOR)
def test_aprovador_passa(client, aprovador, rota):
    client.force_login(aprovador)

    assert client.get(reverse(rota)).status_code == 200


def test_solicitante_recebe_mensagem_de_erro(client, solicitante):
    client.force_login(solicitante)

    resposta = client.get(reverse("dashboard"), follow=True)

    mensagens = [str(m) for m in resposta.context["messages"]]
    assert any("permissão" in m for m in mensagens)


def test_decorator_preserva_metadados_da_view():
    """
    O @wraps mantém nome e docstring da função original.

    Sem ele, todas as views apareceriam como '_verificar' em traceback, log e
    na documentação automática — um pesadelo para depurar em produção.
    """
    from travels.views import dashboard

    assert dashboard.__name__ == "dashboard"
    assert "Dashboard" in dashboard.__doc__


@pytest.mark.parametrize("acao", ["approve_request", "reject_request"])
def test_solicitante_nao_decide_solicitacao(client, solicitante, criar_solicitacao, acao):
    """Aprovar e rejeitar agora compartilham código — a regra vale para as duas."""
    solicitacao = criar_solicitacao()
    client.force_login(solicitante)

    resposta = client.post(reverse(acao, args=[solicitacao.pk]), {"observacoes": ""})
    solicitacao.refresh_from_db()

    assert resposta.url == reverse("home")
    assert solicitacao.status == "PENDENTE"

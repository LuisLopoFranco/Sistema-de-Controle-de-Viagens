"""
Testes do cálculo de combustível.

Fórmula: (quilometragem / consumo_medio) * valor_litro

É a regra de negócio central do sistema — é ela que determina quanto a
empresa paga. Erro aqui vira dinheiro errado no reembolso.
"""

from decimal import Decimal

import pytest

pytestmark = pytest.mark.django_db


def test_calculo_com_valores_exatos(criar_solicitacao):
    """100 km / 10 km por litro = 10 litros. 10 litros x R$ 5,50 = R$ 55,00."""
    solicitacao = criar_solicitacao()

    assert solicitacao.calcular_gasto_total() == Decimal("55.00")


def test_valor_e_gravado_automaticamente_no_save(criar_solicitacao):
    """O campo valor_total_combustivel não é preenchido pelo usuário."""
    solicitacao = criar_solicitacao()
    solicitacao.refresh_from_db()

    assert solicitacao.valor_total_combustivel == Decimal("55.00")


def test_valor_e_recalculado_ao_alterar_quilometragem(criar_solicitacao):
    """Editar a viagem precisa refletir no valor, não manter o antigo."""
    solicitacao = criar_solicitacao()

    solicitacao.quilometragem = Decimal("200.00")
    solicitacao.save()
    solicitacao.refresh_from_db()

    assert solicitacao.valor_total_combustivel == Decimal("110.00")


def test_carro_mais_economico_gasta_menos(criar_solicitacao):
    """Consumo médio maior significa menos litros para a mesma distância."""
    economico = criar_solicitacao(consumo_medio=Decimal("20.00"))

    assert economico.calcular_gasto_total() == Decimal("27.50")


@pytest.mark.xfail(
    reason="Arredondamento explícito ainda não implementado — previsto na Fase 3",
    strict=True,
)
def test_resultado_tem_no_maximo_duas_casas_decimais(criar_solicitacao):
    """
    100 km / 3 km por litro = 33,333... litros.

    Hoje o método devolve um Decimal com 28 casas decimais e deixa o banco
    truncar na gravação. Isso significa que o valor em memória logo após o
    save() é diferente do valor persistido — armadilha clássica em cálculo
    financeiro. A correção é aplicar quantize() com regra de arredondamento
    definida.
    """
    solicitacao = criar_solicitacao(consumo_medio=Decimal("3.00"))

    resultado = solicitacao.calcular_gasto_total()

    assert resultado == resultado.quantize(Decimal("0.01"))

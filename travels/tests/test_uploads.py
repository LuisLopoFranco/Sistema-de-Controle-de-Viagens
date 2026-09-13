"""
Testes da validação de upload de nota fiscal.

Estes testes cobrem a superfície de ataque mais óbvia do sistema: um campo
que aceita arquivo enviado por qualquer usuário autenticado.
"""

from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from travels.uploads import (
    TAMANHO_MAXIMO,
    caminho_nota_fiscal,
    validar_nota_fiscal,
)
from travels.tests.conftest import JPG_VALIDO, PDF_VALIDO, PNG_VALIDO


def arquivo(nome, conteudo):
    return SimpleUploadedFile(nome, conteudo)


# --------------------------------------------------------------------------
# Arquivos que devem ser aceitos
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nome,conteudo",
    [
        ("nota.pdf", PDF_VALIDO),
        ("nota.png", PNG_VALIDO),
        ("nota.jpg", JPG_VALIDO),
        ("nota.jpeg", JPG_VALIDO),
        ("NOTA.PDF", PDF_VALIDO),  # extensão em maiúsculas
    ],
)
def test_aceita_formatos_validos(nome, conteudo):
    validar_nota_fiscal(arquivo(nome, conteudo))


# --------------------------------------------------------------------------
# Arquivos que devem ser rejeitados
# --------------------------------------------------------------------------


def test_rejeita_arquivo_vazio():
    with pytest.raises(ValidationError, match="vazio"):
        validar_nota_fiscal(arquivo("nota.pdf", b""))


def test_rejeita_arquivo_acima_do_limite():
    grande = arquivo("nota.pdf", PDF_VALIDO + b"\x00" * TAMANHO_MAXIMO)

    with pytest.raises(ValidationError, match="excede o limite"):
        validar_nota_fiscal(grande)


@pytest.mark.parametrize("nome", ["script.exe", "planilha.xlsx", "nota.txt", "semextensao"])
def test_rejeita_extensao_nao_permitida(nome):
    with pytest.raises(ValidationError, match="Formato não aceito"):
        validar_nota_fiscal(arquivo(nome, PDF_VALIDO))


def test_rejeita_texto_disfarcado_de_pdf():
    """
    O caso que a validação por extensão não pega.

    Renomear um .txt para .pdf engana qualquer verificação baseada em nome.
    Só a leitura dos primeiros bytes revela a fraude.
    """
    disfarcado = arquivo("nota.pdf", b"isto aqui e texto puro, nao e um PDF")

    with pytest.raises(ValidationError, match="não corresponde"):
        validar_nota_fiscal(disfarcado)


def test_rejeita_html_disfarcado_de_imagem():
    """HTML servido pelo próprio domínio é vetor de XSS armazenado."""
    malicioso = arquivo("foto.png", b"<html><script>alert(1)</script></html>")

    with pytest.raises(ValidationError, match="não corresponde"):
        validar_nota_fiscal(malicioso)


def test_validacao_preserva_a_posicao_do_ponteiro():
    """
    Se o validador consumir o arquivo sem rebobinar, o conteúdo é gravado
    truncado ou vazio. Falha silenciosa e difícil de rastrear.
    """
    enviado = arquivo("nota.pdf", PDF_VALIDO)

    validar_nota_fiscal(enviado)

    enviado.seek(0)
    assert enviado.read() == PDF_VALIDO


# --------------------------------------------------------------------------
# Nomeação dos arquivos gravados
# --------------------------------------------------------------------------


def test_nome_original_e_descartado():
    """Nome vindo do usuário não deve chegar ao disco."""
    caminho = caminho_nota_fiscal(None, "Nota Fiscal do João (1).pdf")

    assert "Nota" not in caminho
    assert " " not in caminho


def test_extensao_e_preservada():
    assert caminho_nota_fiscal(None, "nota.png").endswith(".png")
    assert caminho_nota_fiscal(None, "NOTA.PDF").endswith(".pdf")


def test_nomes_gerados_nao_se_repetem():
    """Nome previsível permitiria adivinhar a URL de documentos de terceiros."""
    gerados = {caminho_nota_fiscal(None, "nota.pdf") for _ in range(50)}

    assert len(gerados) == 50


def test_extensao_desconhecida_vira_bin():
    """Defesa em profundidade: se o validador falhar, o arquivo não fica executável."""
    assert caminho_nota_fiscal(None, "script.php").endswith(".bin")


def test_arquivo_e_organizado_por_ano_e_mes():
    partes = Path(caminho_nota_fiscal(None, "nota.pdf")).parts

    assert partes[0] == "notas_fiscais"
    assert len(partes) == 4  # notas_fiscais / ano / mes / arquivo


# --------------------------------------------------------------------------
# Integração com o model
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_arquivo_gravado_recebe_nome_aleatorio(criar_solicitacao):
    """Fecha o ciclo: o upload_to do model realmente usa a função."""
    solicitacao = criar_solicitacao()

    assert "nota.pdf" not in solicitacao.nota_fiscal.name
    assert solicitacao.nota_fiscal.name.endswith(".pdf")

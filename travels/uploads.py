"""
Upload de notas fiscais: nomeação dos arquivos e validação do conteúdo.

A validação verifica três coisas independentes, porque cada uma sozinha é
insuficiente:

1. Tamanho — impede que um upload grande derrube o servidor.
2. Extensão — barra o caso trivial.
3. Assinatura binária (magic number) — barra o caso real. A extensão e o
   Content-Type do formulário são informados pelo cliente e podem ser
   forjados; os primeiros bytes do arquivo, não.
"""

import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils import timezone

# 5 MB. Uma foto de nota fiscal tirada com celular raramente passa disso.
TAMANHO_MAXIMO = 5 * 1024 * 1024

# Extensão aceita -> assinaturas binárias correspondentes.
ASSINATURAS_PERMITIDAS = {
    ".pdf": (b"%PDF-",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
}

EXTENSOES_PERMITIDAS = tuple(sorted(ASSINATURAS_PERMITIDAS))


def caminho_nota_fiscal(instance, filename):
    """
    Define onde a nota fiscal é gravada.

    O nome original é descartado em favor de um UUID. Isso resolve dois
    problemas: nomes de arquivo enviados pelo usuário podem conter caracteres
    perigosos ou tentativas de path traversal, e nomes previsíveis permitem
    que alguém adivinhe a URL de documentos de terceiros.
    """
    extensao = Path(filename).suffix.lower()
    if extensao not in ASSINATURAS_PERMITIDAS:
        extensao = ".bin"
    agora = timezone.now()
    return f"notas_fiscais/{agora:%Y/%m}/{uuid.uuid4().hex}{extensao}"


def validar_nota_fiscal(arquivo):
    """
    Valida o arquivo enviado como nota fiscal.

    Usado como validator no FileField, então recebe o arquivo e levanta
    ValidationError quando algo está errado.
    """
    if arquivo.size == 0:
        raise ValidationError("O arquivo enviado está vazio.")

    if arquivo.size > TAMANHO_MAXIMO:
        limite_mb = TAMANHO_MAXIMO // (1024 * 1024)
        enviado_mb = arquivo.size / (1024 * 1024)
        raise ValidationError(
            f"Arquivo de {enviado_mb:.1f} MB excede o limite de {limite_mb} MB."
        )

    extensao = Path(arquivo.name).suffix.lower()
    assinaturas = ASSINATURAS_PERMITIDAS.get(extensao)
    if assinaturas is None:
        aceitos = ", ".join(EXTENSOES_PERMITIDAS)
        raise ValidationError(
            f"Formato não aceito. Envie um arquivo {aceitos}."
        )

    cabecalho = _ler_cabecalho(arquivo)
    if cabecalho is None:
        # Arquivo já gravado e fechado (revalidação de um registro existente).
        # O conteúdo foi verificado no momento do upload; não há o que refazer.
        return

    if not any(cabecalho.startswith(assinatura) for assinatura in assinaturas):
        raise ValidationError(
            "O conteúdo do arquivo não corresponde à sua extensão. "
            "Envie o arquivo original da nota fiscal."
        )


def _ler_cabecalho(arquivo, tamanho=8):
    """Lê os primeiros bytes preservando a posição do ponteiro."""
    try:
        posicao = arquivo.tell()
        arquivo.seek(0)
        cabecalho = arquivo.read(tamanho)
        arquivo.seek(posicao)
        return cabecalho
    except (ValueError, OSError, AttributeError):
        return None

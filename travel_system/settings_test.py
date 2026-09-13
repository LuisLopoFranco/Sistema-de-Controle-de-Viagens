"""
Configurações usadas pela suíte de testes.

O settings.py exige SECRET_KEY sem valor padrão, de propósito: a aplicação
deve falhar alto se a variável não existir. Isso é bom em produção, mas
impede rodar os testes onde não há arquivo .env — em CI, por exemplo.

Este módulo define as variáveis necessárias e só então importa o settings
real, que passa a encontrá-las já no ambiente.
"""

import os

os.environ.setdefault("SECRET_KEY", "chave-apenas-para-testes-nao-usar-em-producao")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

from .settings import *  # noqa: E402,F403

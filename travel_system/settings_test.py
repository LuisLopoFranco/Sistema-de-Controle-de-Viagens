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

# O WhiteNoise serve os estáticos já processados pelo collectstatic, que não
# roda na suíte. Sem estas duas linhas, cada teste que renderiza template
# emite "No directory at: staticfiles/" — ruído que esconde warning de
# verdade. Servir estático não é o que estes testes verificam.
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405
STORAGES = {  # noqa: F405
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

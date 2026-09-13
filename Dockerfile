# Imagem slim: a completa traz compiladores e ferramentas que a aplicação não
# usa em execução, aumentando o tamanho e a superfície de ataque.
FROM python:3.13-slim

# Não gera .pyc (o container é descartável) e não bufferiza a saída, para que
# o log apareça em tempo real em vez de sair em blocos.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libpq5 é a biblioteca cliente do PostgreSQL, exigida pelo psycopg em tempo
# de execução. Limpar a lista de pacotes na mesma camada evita carregá-la
# para dentro da imagem final.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar só as dependências primeiro faz o Docker reaproveitar esta camada
# enquanto o requirements.txt não mudar. Sem isso, qualquer alteração no
# código reinstalaria tudo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuário sem privilégios. Rodar como root dentro do container significa que
# uma falha na aplicação vira root no container.
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R app:app /app
USER app

EXPOSE 8000

# 3 workers é um ponto de partida razoável; ajuste conforme a CPU disponível.
# O timeout maior acomoda a geração de PDF, que pode demorar.
CMD ["gunicorn", "travel_system.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-"]

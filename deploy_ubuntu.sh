#!/bin/bash

###############################################################################
# Script de Deploy Automático - Sistema de Controle de Viagens
# Ubuntu 24.04.2 - Servidor Interno
###############################################################################

set -e  # Sair em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verificar se está rodando como root
if [[ $EUID -ne 0 ]]; then
   print_error "Este script precisa ser executado como root (use sudo)"
   exit 1
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Sistema de Controle de Viagens - Deploy Automático        ║"
echo "║                  Ubuntu 24.04.2 (Interno)                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Solicitar informações do usuário
print_message "Configuração inicial - responda as perguntas abaixo:"
echo ""

read -p "IP interno do servidor (ex: 192.168.1.100): " SERVER_IP
read -p "URL do repositório Git: " GIT_REPO
read -sp "Senha para o banco de dados PostgreSQL: " DB_PASSWORD
echo ""
read -sp "SECRET_KEY do Django (deixe vazio para gerar automaticamente): " SECRET_KEY
echo ""

# Gerar SECRET_KEY se não fornecida
if [ -z "$SECRET_KEY" ]; then
    print_message "Gerando SECRET_KEY aleatória..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
fi

print_message "Iniciando instalação..."
sleep 2

# 1. Atualizar sistema
print_message "Atualizando sistema operacional..."
apt update -qq
apt upgrade -y -qq

# 2. Instalar dependências
print_message "Instalando dependências do sistema..."
apt install -y -qq python3 python3-pip python3-venv python3-dev \
    nginx postgresql postgresql-contrib \
    git curl supervisor ufw

# 3. Configurar PostgreSQL
print_message "Configurando banco de dados PostgreSQL..."
sudo -u postgres psql <<EOF
CREATE DATABASE travel_system;
CREATE USER travel_user WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE travel_user SET client_encoding TO 'utf8';
ALTER ROLE travel_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE travel_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE travel_system TO travel_user;
\q
EOF

# 4. Criar usuário para aplicação
print_message "Criando usuário da aplicação..."
if id "travelapp" &>/dev/null; then
    print_warning "Usuário travelapp já existe"
else
    useradd -m -s /bin/bash travelapp
fi

# 5. Clonar repositório
print_message "Clonando repositório..."
cd /home/travelapp

if [ -d "app" ]; then
    print_warning "Diretório app já existe, atualizando..."
    cd app
    sudo -u travelapp git pull
else
    sudo -u travelapp git clone $GIT_REPO app
    cd app
fi

# 6. Criar ambiente virtual e instalar dependências
print_message "Criando ambiente virtual Python..."
sudo -u travelapp python3 -m venv venv

print_message "Instalando dependências Python..."
sudo -u travelapp bash -c "source venv/bin/activate && pip install --upgrade pip -q"
sudo -u travelapp bash -c "source venv/bin/activate && pip install -r requirements.txt -q"
sudo -u travelapp bash -c "source venv/bin/activate && pip install gunicorn psycopg2-binary python-decouple -q"

# 7. Criar arquivo .env
print_message "Criando arquivo de configuração .env..."
cat > /home/travelapp/app/.env <<EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${SERVER_IP},localhost,127.0.0.1

# Database
DB_NAME=travel_system
DB_USER=travel_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=5432
EOF

chown travelapp:travelapp /home/travelapp/app/.env
chmod 600 /home/travelapp/app/.env

# 8. Atualizar settings.py para produção
print_message "Configurando Django para produção..."
cat > /home/travelapp/app/travel_system/settings_prod.py <<'EOF'
from .settings import *
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='travel_system'),
        'USER': config('DB_USER', default='travel_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Security
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = False  # Mude para True se usar HTTPS
CSRF_COOKIE_SECURE = False     # Mude para True se usar HTTPS

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
EOF

# Ajustar manage.py para usar settings_prod
print_message "Configurando manage.py para produção..."
sudo -u travelapp bash -c "cd /home/travelapp/app && sed -i \"s/'travel_system.settings'/'travel_system.settings_prod'/g\" manage.py"

# 9. Executar migrações
print_message "Executando migrações do banco de dados..."
sudo -u travelapp bash -c "cd /home/travelapp/app && source venv/bin/activate && python manage.py migrate"

# 10. Coletar arquivos estáticos
print_message "Coletando arquivos estáticos..."
sudo -u travelapp bash -c "cd /home/travelapp/app && source venv/bin/activate && python manage.py collectstatic --noinput"

# 11. Criar diretórios necessários
print_message "Criando diretórios necessários..."
mkdir -p /home/travelapp/app/logs
mkdir -p /home/travelapp/app/media
mkdir -p /home/travelapp/backups
chown -R travelapp:www-data /home/travelapp/app
chmod -R 755 /home/travelapp/app
chmod -R 775 /home/travelapp/app/media
chmod -R 775 /home/travelapp/app/logs

# 12. Configurar serviço systemd
print_message "Configurando serviço systemd..."
cat > /etc/systemd/system/travelapp.service <<EOF
[Unit]
Description=Travel System Gunicorn Daemon
After=network.target

[Service]
User=travelapp
Group=www-data
WorkingDirectory=/home/travelapp/app
Environment="PATH=/home/travelapp/app/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=travel_system.settings_prod"
EnvironmentFile=/home/travelapp/app/.env
ExecStart=/home/travelapp/app/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/travelapp/app/travel_system.sock \
          --timeout 120 \
          --access-logfile /home/travelapp/app/logs/gunicorn-access.log \
          --error-logfile /home/travelapp/app/logs/gunicorn-error.log \
          travel_system.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable travelapp
systemctl start travelapp

# 13. Configurar Nginx
print_message "Configurando Nginx..."
cat > /etc/nginx/sites-available/travelapp <<EOF
server {
    listen 80;
    server_name ${SERVER_IP};

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /home/travelapp/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/travelapp/app/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/travelapp/app/travel_system.sock;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_redirect off;
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }

    access_log /var/log/nginx/travelapp-access.log;
    error_log /var/log/nginx/travelapp-error.log;
}
EOF

ln -sf /etc/nginx/sites-available/travelapp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 14. Configurar firewall
print_message "Configurando firewall UFW..."
ufw --force enable
ufw allow 'Nginx Full'
ufw allow OpenSSH

# 15. Criar script de backup
print_message "Criando script de backup..."
cat > /home/travelapp/backup.sh <<'BACKUPEOF'
#!/bin/bash
BACKUP_DIR="/home/travelapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="travel_system"
DB_USER="travel_user"

# Backup do banco de dados
sudo -u postgres pg_dump $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos de media
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C /home/travelapp/app media/

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "media_backup_*.tar.gz" -mtime +7 -delete

echo "Backup realizado: $DATE"
BACKUPEOF

chmod +x /home/travelapp/backup.sh
chown travelapp:travelapp /home/travelapp/backup.sh

# Adicionar ao cron
(crontab -l 2>/dev/null; echo "0 2 * * * /home/travelapp/backup.sh >> /home/travelapp/backups/backup.log 2>&1") | crontab -

print_message "Criando usuários de demonstração..."
sudo -u travelapp bash -c "cd /home/travelapp/app && source venv/bin/activate && python create_demo_users.py" || print_warning "Não foi possível criar usuários de demonstração"

# Resumo final
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   INSTALAÇÃO CONCLUÍDA!                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
print_message "Sistema instalado com sucesso!"
echo ""
echo "Informações de acesso:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "URL do Sistema: http://${SERVER_IP}"
echo "URL Admin:      http://${SERVER_IP}/admin"
echo ""
echo "Usuários de demonstração criados:"
echo "  Admin:        admin / admin123"
echo "  Aprovador:    aprovador / aprovador123"
echo "  Solicitante:  solicitante / solicitante123"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Próximos passos:"
echo "1. Acesse http://${SERVER_IP}/admin"
echo "2. Faça login com admin / admin123"
echo "3. Vá em 'Configurações do Sistema'"
echo "4. Configure a URL da aplicação para: http://${SERVER_IP}"
echo ""
echo "Comandos úteis:"
echo "  Ver logs:      sudo journalctl -u travelapp -f"
echo "  Reiniciar:     sudo systemctl restart travelapp"
echo "  Status:        sudo systemctl status travelapp"
echo "  Backup manual: sudo /home/travelapp/backup.sh"
echo ""
print_message "Deploy finalizado! Acesse o sistema e configure conforme necessário."

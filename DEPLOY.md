# Guia de Deploy - Ubuntu 24.04.2 (Servidor Interno)

Este guia explica como fazer o deploy do Sistema de Controle de Viagens em um servidor Ubuntu 24.04.2 para uso interno na rede local da empresa.

## 📋 Pré-requisitos

- Servidor Ubuntu 24.04.2 (físico ou VM)
- Acesso root ou sudo
- IP interno estático configurado (ex: 192.168.1.100)
- Acesso SSH ao servidor

## 🚀 Instalação Automática (Recomendado)

### Opção 1: Script Automático

```bash
# No servidor Ubuntu, execute:
wget https://raw.githubusercontent.com/SEU-USUARIO/Sistema-de-Controle-de-Viagens/main/deploy_ubuntu.sh
chmod +x deploy_ubuntu.sh
sudo ./deploy_ubuntu.sh
```

**OU** copie o script manualmente (veja arquivo `deploy_ubuntu.sh` neste repositório)

---

## 📝 Instalação Manual (Passo a Passo)

### 1. Atualizar o Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Instalar Dependências do Sistema

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    nginx postgresql postgresql-contrib \
    git curl supervisor
```

### 3. Configurar PostgreSQL

```bash
# Acessar o PostgreSQL
sudo -u postgres psql

# Dentro do PostgreSQL, execute:
CREATE DATABASE travel_system;
CREATE USER travel_user WITH PASSWORD 'SUA_SENHA_FORTE_AQUI';
ALTER ROLE travel_user SET client_encoding TO 'utf8';
ALTER ROLE travel_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE travel_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE travel_system TO travel_user;

# Sair do PostgreSQL
\q
```

### 4. Criar Usuário para a Aplicação

```bash
# Criar usuário sem shell (segurança)
sudo useradd -m -s /bin/bash travelapp
sudo su - travelapp
```

### 5. Clonar o Repositório

```bash
# Como usuário travelapp
cd /home/travelapp
git clone https://github.com/SEU-USUARIO/Sistema-de-Controle-de-Viagens.git app
cd app
```

### 6. Criar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 7. Instalar Dependências Python

```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt

# Instalar dependências adicionais para produção
pip install gunicorn psycopg2-binary
```

### 8. Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env
nano .env
```

Cole o seguinte conteúdo (ajuste conforme necessário):

```bash
# .env
SECRET_KEY=sua-chave-secreta-super-longa-e-aleatoria-aqui
DEBUG=False
ALLOWED_HOSTS=192.168.1.100,localhost,127.0.0.1

# Database
DB_NAME=travel_system
DB_USER=travel_user
DB_PASSWORD=SUA_SENHA_FORTE_AQUI
DB_HOST=localhost
DB_PORT=5432
```

**IMPORTANTE**: Gere uma SECRET_KEY segura:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 9. Atualizar settings.py para Produção

Crie um arquivo `travel_system/settings_prod.py`:

```bash
nano travel_system/settings_prod.py
```

Cole o conteúdo (veja arquivo separado abaixo).

### 10. Executar Migrações e Coletar Arquivos Estáticos

```bash
# Ativar ambiente virtual se não estiver ativo
source venv/bin/activate

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar superusuário
python manage.py createsuperuser

# Ou criar usuários de demonstração
python create_demo_users.py
```

### 11. Testar Gunicorn

```bash
# Testar se o Gunicorn funciona
gunicorn --bind 0.0.0.0:8000 travel_system.wsgi:application
```

Acesse http://IP-DO-SERVIDOR:8000 para testar. Se funcionar, pressione Ctrl+C.

### 12. Configurar Gunicorn como Serviço (Systemd)

```bash
# Sair do usuário travelapp
exit

# Como root/sudo, criar arquivo de serviço
sudo nano /etc/systemd/system/travelapp.service
```

Cole o seguinte conteúdo:

```ini
[Unit]
Description=Travel System Gunicorn Daemon
After=network.target

[Service]
User=travelapp
Group=www-data
WorkingDirectory=/home/travelapp/app
Environment="PATH=/home/travelapp/app/venv/bin"
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
```

```bash
# Criar diretório de logs
sudo mkdir -p /home/travelapp/app/logs
sudo chown -R travelapp:www-data /home/travelapp/app/logs

# Habilitar e iniciar o serviço
sudo systemctl start travelapp
sudo systemctl enable travelapp

# Verificar status
sudo systemctl status travelapp
```

### 13. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/travelapp
```

Cole o seguinte conteúdo:

```nginx
server {
    listen 80;
    server_name 192.168.1.100;  # Altere para o IP do seu servidor

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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }

    # Logs
    access_log /var/log/nginx/travelapp-access.log;
    error_log /var/log/nginx/travelapp-error.log;
}
```

```bash
# Ativar o site
sudo ln -s /etc/nginx/sites-available/travelapp /etc/nginx/sites-enabled/

# Remover site padrão do Nginx (opcional)
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração do Nginx
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 14. Configurar Firewall (UFW)

```bash
# Habilitar firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable

# Verificar status
sudo ufw status
```

### 15. Ajustar Permissões

```bash
# Dar permissões corretas aos diretórios
sudo chown -R travelapp:www-data /home/travelapp/app
sudo chmod -R 755 /home/travelapp/app
sudo chmod -R 775 /home/travelapp/app/media
sudo chmod -R 755 /home/travelapp/app/staticfiles
```

---

## 🔧 Configurações Finais

### 1. Configurar URL no Sistema

1. Acesse: `http://192.168.1.100/admin`
2. Faça login com o superusuário
3. Vá em "Configurações do Sistema"
4. Configure a "URL da Aplicação" para: `http://192.168.1.100`

### 2. Configurar Backup Automático

```bash
sudo nano /home/travelapp/backup.sh
```

Cole o script de backup (veja arquivo separado).

```bash
# Dar permissão de execução
sudo chmod +x /home/travelapp/backup.sh

# Adicionar ao cron para backup diário às 2h da manhã
sudo crontab -e

# Adicionar linha:
0 2 * * * /home/travelapp/backup.sh
```

---

## 🔄 Comandos Úteis de Manutenção

### Reiniciar Aplicação

```bash
sudo systemctl restart travelapp
```

### Ver Logs da Aplicação

```bash
# Logs do Gunicorn
sudo tail -f /home/travelapp/app/logs/gunicorn-error.log
sudo tail -f /home/travelapp/app/logs/gunicorn-access.log

# Logs do Nginx
sudo tail -f /var/log/nginx/travelapp-error.log
sudo tail -f /var/log/nginx/travelapp-access.log

# Logs do systemd
sudo journalctl -u travelapp -f
```

### Atualizar Aplicação

```bash
sudo su - travelapp
cd app
source venv/bin/activate

# Puxar atualizações
git pull

# Instalar dependências (se houver)
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Sair e reiniciar
exit
sudo systemctl restart travelapp
```

### Backup Manual

```bash
sudo su - travelapp
cd /home/travelapp
./backup.sh
```

---

## 🐛 Resolução de Problemas

### Erro 502 Bad Gateway

```bash
# Verificar se o Gunicorn está rodando
sudo systemctl status travelapp

# Verificar logs
sudo journalctl -u travelapp -n 50
```

### Erro de Permissão em Arquivos

```bash
sudo chown -R travelapp:www-data /home/travelapp/app
sudo chmod -R 775 /home/travelapp/app/media
```

### Erro de Banco de Dados

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
sudo -u postgres psql -d travel_system
```

### Arquivos Estáticos Não Carregam

```bash
sudo su - travelapp
cd app
source venv/bin/activate
python manage.py collectstatic --noinput
exit
sudo systemctl restart nginx
```

---

## 📊 Monitoramento

### Verificar Status dos Serviços

```bash
sudo systemctl status travelapp
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Verificar Uso de Recursos

```bash
# CPU e Memória
htop

# Espaço em disco
df -h

# Conexões ativas
sudo netstat -tulpn | grep :80
```

---

## 🔒 Segurança

### Recomendações Adicionais

1. **Mantenha o sistema atualizado**:
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Configure senha forte para PostgreSQL**

3. **Mantenha backups regulares**

4. **Restrinja acesso SSH** (se necessário):
```bash
sudo nano /etc/ssh/sshd_config
# Alterar porta, desabilitar root login, etc.
```

5. **Configure fail2ban** (opcional):
```bash
sudo apt install fail2ban
```

---

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs (seção "Comandos Úteis")
2. Consulte a seção "Resolução de Problemas"
3. Verifique as permissões de arquivos e diretórios
4. Certifique-se de que todos os serviços estão rodando

---

## 📝 Checklist Pós-Deploy

- [ ] Sistema acessível via `http://IP-DO-SERVIDOR`
- [ ] Login funcionando
- [ ] Upload de arquivos funcionando
- [ ] Criação de solicitações funcionando
- [ ] Dashboard carregando corretamente
- [ ] Painel admin acessível em `/admin`
- [ ] URL configurada no painel admin
- [ ] Backup automático configurado
- [ ] Serviços configurados para iniciar automaticamente
- [ ] Firewall configurado
- [ ] Logs funcionando corretamente

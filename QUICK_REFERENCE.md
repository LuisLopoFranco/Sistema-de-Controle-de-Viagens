# Guia Rápido de Referência - Sistema de Controle de Viagens

## 🚀 Deploy Rápido (Ubuntu 24.04.2)

```bash
# 1. Baixar e executar script de deploy
wget https://raw.githubusercontent.com/SEU-USUARIO/repo/main/deploy_ubuntu.sh
chmod +x deploy_ubuntu.sh
sudo ./deploy_ubuntu.sh

# 2. Acesse o sistema
http://IP-DO-SERVIDOR
```

---

## 📋 Comandos Essenciais

### Gerenciamento da Aplicação

```bash
# Ver logs em tempo real
sudo journalctl -u travelapp -f

# Reiniciar aplicação
sudo systemctl restart travelapp

# Parar aplicação
sudo systemctl stop travelapp

# Iniciar aplicação
sudo systemctl start travelapp

# Ver status
sudo systemctl status travelapp
```

### Gerenciamento do Nginx

```bash
# Reiniciar Nginx
sudo systemctl restart nginx

# Testar configuração
sudo nginx -t

# Ver logs
sudo tail -f /var/log/nginx/travelapp-error.log
sudo tail -f /var/log/nginx/travelapp-access.log
```

### Banco de Dados

```bash
# Acessar PostgreSQL
sudo -u postgres psql -d travel_system

# Backup manual
sudo -u postgres pg_dump travel_system > backup.sql

# Restaurar backup
sudo -u postgres psql travel_system < backup.sql
```

### Atualizar Sistema

```bash
# Método 1: Script automático
sudo su - travelapp
cd app
./update_app.sh

# Método 2: Manual
sudo su - travelapp
cd app
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
exit
sudo systemctl restart travelapp
```

---

## 🔧 Manutenção

### Backup

```bash
# Backup automático (configurado no cron)
sudo /home/travelapp/backup.sh

# Localização dos backups
/home/travelapp/backups/

# Ver log de backups
cat /home/travelapp/backups/backup.log
```

### Logs

```bash
# Logs da aplicação
sudo tail -f /home/travelapp/app/logs/gunicorn-error.log
sudo tail -f /home/travelapp/app/logs/gunicorn-access.log

# Logs do Nginx
sudo tail -f /var/log/nginx/travelapp-error.log

# Logs do sistema
sudo journalctl -u travelapp -n 100
```

### Limpeza

```bash
# Limpar arquivos estáticos antigos
sudo su - travelapp
cd app
source venv/bin/activate
python manage.py collectstatic --clear --noinput
exit

# Limpar backups antigos (mantém últimos 7 dias)
find /home/travelapp/backups -name "*.sql" -mtime +7 -delete
find /home/travelapp/backups -name "*.tar.gz" -mtime +7 -delete
```

---

## 🐛 Resolução de Problemas

### Erro 502 Bad Gateway

```bash
# 1. Verificar se Gunicorn está rodando
sudo systemctl status travelapp

# 2. Verificar logs
sudo journalctl -u travelapp -n 50

# 3. Reiniciar serviço
sudo systemctl restart travelapp

# 4. Verificar permissões do socket
ls -l /home/travelapp/app/travel_system.sock
```

### Arquivos estáticos não carregam

```bash
sudo su - travelapp
cd app
source venv/bin/activate
python manage.py collectstatic --noinput
exit
sudo systemctl restart nginx
```

### Erro de permissão em uploads

```bash
sudo chown -R travelapp:www-data /home/travelapp/app/media
sudo chmod -R 775 /home/travelapp/app/media
sudo systemctl restart travelapp
```

### Banco de dados não conecta

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar conexão
sudo -u postgres psql -d travel_system -c "\conninfo"

# Verificar .env
cat /home/travelapp/app/.env | grep DB_
```

### Aplicação lenta

```bash
# Verificar uso de recursos
htop

# Verificar conexões PostgreSQL
sudo -u postgres psql -d travel_system -c "SELECT count(*) FROM pg_stat_activity;"

# Aumentar workers do Gunicorn (editar service)
sudo nano /etc/systemd/system/travelapp.service
# Alterar --workers 3 para --workers 5
sudo systemctl daemon-reload
sudo systemctl restart travelapp
```

---

## 👤 Gerenciamento de Usuários

### Painel Admin

```bash
# Acesse: http://IP-DO-SERVIDOR/admin
# Login: admin / admin123 (altere após primeiro acesso!)
```

### Criar superusuário via terminal

```bash
sudo su - travelapp
cd app
source venv/bin/activate
python manage.py createsuperuser
```

### Alterar senha de usuário

```bash
sudo su - travelapp
cd app
source venv/bin/activate
python manage.py changepassword USERNAME
```

---

## 📊 Monitoramento

### Verificar espaço em disco

```bash
df -h
du -sh /home/travelapp/app/media/*
```

### Verificar memória e CPU

```bash
htop
# ou
top
```

### Verificar conexões ativas

```bash
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep gunicorn
```

### Estatísticas do Nginx

```bash
# Requisições por IP
sudo cat /var/log/nginx/travelapp-access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# Páginas mais acessadas
sudo cat /var/log/nginx/travelapp-access.log | awk '{print $7}' | sort | uniq -c | sort -rn | head -10
```

---

## 🔒 Segurança

### Atualizar sistema

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot  # Se necessário
```

### Verificar firewall

```bash
sudo ufw status
```

### Alterar senha do PostgreSQL

```bash
sudo -u postgres psql
\password travel_user
# Digite nova senha
\q

# Atualizar .env
sudo nano /home/travelapp/app/.env
# Altere DB_PASSWORD

# Reiniciar aplicação
sudo systemctl restart travelapp
```

### Logs de acesso suspeitos

```bash
# Ver tentativas de acesso ao admin
sudo grep "/admin" /var/log/nginx/travelapp-access.log | tail -50

# Ver erros 404
sudo grep " 404 " /var/log/nginx/travelapp-access.log | tail -20
```

---

## 📞 Checklist de Manutenção

### Diário
- [ ] Verificar logs de erro
- [ ] Verificar se aplicação está respondendo

### Semanal
- [ ] Verificar backups foram criados
- [ ] Verificar espaço em disco
- [ ] Revisar logs de acesso

### Mensal
- [ ] Atualizar sistema operacional
- [ ] Revisar usuários ativos
- [ ] Limpar logs antigos
- [ ] Testar restauração de backup

---

## 🆘 Suporte Rápido

| Problema | Solução |
|----------|---------|
| Site fora do ar | `sudo systemctl restart travelapp nginx` |
| Upload não funciona | Verificar permissões da pasta media |
| Lentidão | Verificar logs e recursos do servidor |
| Erro 500 | Ver logs em `/home/travelapp/app/logs/` |
| Banco de dados | Ver logs do PostgreSQL |

---

## 📝 Variáveis de Ambiente (.env)

Localização: `/home/travelapp/app/.env`

```bash
SECRET_KEY=...           # Chave secreta Django
DEBUG=False              # Sempre False em produção
ALLOWED_HOSTS=...        # IPs permitidos
DB_NAME=travel_system    # Nome do banco
DB_USER=travel_user      # Usuário do banco
DB_PASSWORD=...          # Senha do banco
DB_HOST=localhost        # Host do banco
DB_PORT=5432             # Porta do banco
```

---

## 🔗 URLs Importantes

- Sistema: `http://IP-DO-SERVIDOR/`
- Admin: `http://IP-DO-SERVIDOR/admin/`
- Login: `http://IP-DO-SERVIDOR/login/`
- Cadastro: `http://IP-DO-SERVIDOR/register/`

---

## 📚 Documentação Completa

Para mais detalhes, consulte:
- `DEPLOY.md` - Guia completo de deploy
- `README.md` - Documentação geral do sistema
- `INSTALL.md` - Guia de instalação rápida

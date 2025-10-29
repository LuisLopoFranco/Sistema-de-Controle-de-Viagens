#!/bin/bash

###############################################################################
# Script de Atualização - Sistema de Controle de Viagens
# Use este script para atualizar o sistema após alterações no código
###############################################################################

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

echo "════════════════════════════════════════════════════════"
echo "  Atualizando Sistema de Controle de Viagens"
echo "════════════════════════════════════════════════════════"
echo ""

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "ERRO: Execute este script do diretório raiz da aplicação"
    exit 1
fi

# Fazer backup antes da atualização
print_message "Criando backup antes da atualização..."
sudo /home/travelapp/backup.sh

# Atualizar código do repositório
print_message "Baixando atualizações do repositório..."
git fetch origin
git pull origin $(git branch --show-current)

# Ativar ambiente virtual
print_message "Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar dependências
print_message "Atualizando dependências Python..."
pip install -r requirements.txt --upgrade

# Executar migrações
print_message "Executando migrações do banco de dados..."
python manage.py migrate

# Coletar arquivos estáticos
print_message "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Reiniciar serviços
print_message "Reiniciando aplicação..."
sudo systemctl restart travelapp

# Aguardar inicialização
sleep 3

# Verificar status
print_message "Verificando status..."
sudo systemctl status travelapp --no-pager

echo ""
print_message "Atualização concluída!"
echo ""
echo "Verificações recomendadas:"
echo "  1. Acesse o sistema e teste as funcionalidades"
echo "  2. Verifique os logs: sudo journalctl -u travelapp -n 50"
echo "  3. Teste upload de arquivos"
echo ""

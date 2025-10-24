# Guia de Instalação Rápida

## Instalação Local (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd Sistema-de-Controle-de-Viagens

# 2. Crie um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute as migrações
python manage.py migrate

# 5. Crie usuários de demonstração
python create_demo_users.py

# 6. Inicie o servidor
python manage.py runserver

# 7. Acesse http://127.0.0.1:8000
```

## Usuários de Teste

Após executar `create_demo_users.py`, você terá:

**APROVADORES:**
- admin / admin123 (Superusuário)
- aprovador / aprovador123

**SOLICITANTES:**
- solicitante / solicitante123
- colaborador1 / senha123
- colaborador2 / senha223
- colaborador3 / senha323

## Estrutura de Diretórios Criados

Após a instalação, serão criados automaticamente:
- `media/` - Armazenamento de notas fiscais enviadas
- `db.sqlite3` - Banco de dados SQLite
- `travels/migrations/` - Arquivos de migração do banco

## Painel Administrativo

Acesse: http://127.0.0.1:8000/admin
Login: admin / admin123

No painel você pode:
- Gerenciar usuários
- Alterar perfis (Solicitante ↔ Aprovador)
- Visualizar todas as solicitações
- Gerenciar contas bancárias

## Fluxo de Uso

### Como Solicitante:
1. Faça login
2. Cadastre sua conta bancária (menu "Conta Bancária")
3. Crie uma nova solicitação (menu "Nova Solicitação")
4. Acompanhe o status em "Minhas Solicitações"

### Como Aprovador:
1. Faça login
2. Visualize o dashboard com estatísticas
3. Acesse "Todas as Solicitações"
4. Aprove ou rejeite solicitações pendentes

## Problemas Comuns

### Erro ao fazer upload de arquivo
- Verifique se o diretório `media/` existe e tem permissão de escrita
- Em produção, configure um servidor de arquivos (nginx, S3, etc.)

### Erro de static files
- Execute: `python manage.py collectstatic`
- Verifique se o diretório `static/` existe

### Banco de dados não criado
- Execute: `python manage.py migrate`
- Verifique permissões de escrita no diretório

## Próximos Passos

Para colocar em produção, consulte o README.md, seção "Configurar para Produção".

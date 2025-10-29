# Sistema de Controle de Viagens

Sistema web desenvolvido em Python/Django para gerenciamento de solicitações de reembolso de viagens, com fluxo de aprovação e dashboard de análise.

## Funcionalidades

### Para Solicitantes
- Cadastro e autenticação de usuários
- Registro de dados bancários para reembolso
- Criação de solicitações de viagem com:
  - Destino e data da viagem
  - Quilometragem rodada
  - Valor do litro de combustível
  - Consumo médio do veículo (km/L)
  - **Cálculo automático** do valor total (em tempo real)
  - Upload de nota fiscal
  - Seleção de conta bancária para reembolso
- Visualização de suas próprias solicitações
- Acompanhamento do status (Pendente, Aprovada, Rejeitada)
- Dashboard com estatísticas pessoais

### Para Aprovadores
- Visualização de todas as solicitações
- Aprovação ou rejeição de viagens
- Adição de observações nas aprovações/rejeições
- Dashboard completo com:
  - Estatísticas gerais (total de solicitações, pendentes, aprovadas, rejeitadas)
  - Total de gastos aprovados
  - Ranking de colaboradores por valor gasto
  - Ranking de colaboradores por número de viagens
  - Solicitações recentes
- Filtros por período, status e colaborador
- Acesso bloqueado ao cadastro de conta bancária (apenas para solicitantes)

### Para Administradores (Superusuário)
- Todas as funcionalidades de aprovador
- Gerenciamento completo de usuários:
  - Criar novos usuários
  - Ativar/Inativar usuários em massa
  - Alterar tipo de usuário (Solicitante ↔ Aprovador)
  - Redefinir senhas de usuários
- Configurações do sistema:
  - Configurar URL da aplicação
  - Definir consumo médio padrão dos veículos
  - Configurar nome da empresa

## Tecnologias Utilizadas

- **Python 3.x**
- **Django 4.2.7** - Framework web
- **Bootstrap 5.3** - Interface responsiva e moderna
- **SQLite** - Banco de dados (desenvolvimento)
- **Pillow** - Processamento de imagens

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd Sistema-de-Controle-de-Viagens
```

2. **Crie e ative um ambiente virtual (recomendado)**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Execute as migrações do banco de dados**
```bash
python manage.py migrate
```

5. **Crie usuários de demonstração (opcional)**
```bash
python create_demo_users.py
```

Este script criará os seguintes usuários para teste:
- **admin** / admin123 (Aprovador + Superusuário)
- **aprovador** / aprovador123 (Aprovador)
- **solicitante** / solicitante123 (Solicitante)
- **colaborador1** / senha123 (Solicitante)
- **colaborador2** / senha223 (Solicitante)
- **colaborador3** / senha323 (Solicitante)

6. **Inicie o servidor de desenvolvimento**
```bash
python manage.py runserver
```

7. **Acesse o sistema**
Abra seu navegador e acesse: http://127.0.0.1:8000

## Uso do Sistema

### Primeiro Acesso

1. Acesse http://127.0.0.1:8000
2. Faça login com um dos usuários criados ou cadastre-se
3. Se for novo usuário, você será criado como **Solicitante** por padrão

### Para Solicitantes

1. **Cadastrar Conta Bancária** (obrigatório antes da primeira solicitação)
   - Acesse "Conta Bancária" no menu lateral
   - Preencha os dados bancários para reembolso

2. **Criar Solicitação de Viagem**
   - Clique em "Nova Solicitação"
   - Preencha os dados da viagem:
     - Destino
     - Data da viagem
     - Quilometragem rodada
     - Valor do litro de combustível
     - Consumo médio do veículo (pré-preenchido automaticamente)
   - O sistema calculará automaticamente o valor total em tempo real
   - Faça upload da nota fiscal (PDF, JPG ou PNG)
   - Selecione a conta bancária para reembolso
   - Clique em "Criar Solicitação"

3. **Acompanhar Solicitações**
   - Acesse "Minhas Solicitações"
   - Visualize o status de cada solicitação
   - Clique em "Ver" para detalhes completos

### Para Aprovadores

1. **Dashboard**
   - Visualize estatísticas gerais do sistema
   - Acompanhe rankings e gastos totais
   - Use filtros de período para análises específicas

2. **Aprovar/Rejeitar Solicitações**
   - Acesse "Todas as Solicitações"
   - Use filtros para encontrar solicitações específicas
   - Clique em "Ver" para analisar os detalhes
   - Clique em "Aprovar" ou "Rejeitar"
   - Adicione observações (opcional para aprovação, recomendado para rejeição)

### Painel Administrativo

Acesse http://127.0.0.1:8000/admin com as credenciais de superusuário para:

**Gerenciamento de Usuários:**
- Criar novos usuários manualmente
- Ativar/Inativar usuários (ação em massa)
- Alterar perfis de usuário: Solicitante ↔ Aprovador (ação em massa)
- Redefinir senhas de usuários
- Visualizar histórico de atividades

**Configurações do Sistema:**
- Configurar URL da aplicação (para acesso interno/externo)
- Definir consumo médio padrão dos veículos (usado como valor inicial)
- Configurar nome da empresa
- Personalizar nome da aplicação

**Gerenciamento de Dados:**
- Visualizar e editar todas as solicitações de viagem
- Gerenciar contas bancárias
- Acessar logs e auditoria do sistema

## Cálculo Automático de Gastos

O sistema calcula automaticamente o valor total do gasto com combustível usando a seguinte fórmula:

```
Valor Total = (Quilometragem ÷ Consumo Médio) × Valor do Litro
```

**Exemplo:**
- Quilometragem: 150 km
- Consumo médio: 10 km/L
- Valor do litro: R$ 5,50

```
Litros gastos = 150 ÷ 10 = 15 litros
Valor total = 15 × 5,50 = R$ 82,50
```

O cálculo é realizado:
- **Em tempo real** durante o preenchimento do formulário (JavaScript)
- **No backend** antes de salvar no banco de dados (Python)
- Usando o consumo médio configurado pelo administrador como padrão

## Estrutura do Projeto

```
Sistema-de-Controle-de-Viagens/
├── travel_system/          # Configurações do projeto Django
│   ├── settings.py        # Configurações gerais
│   ├── urls.py            # URLs principais
│   └── wsgi.py            # WSGI para produção
├── travels/               # App principal
│   ├── models.py         # Modelos de dados
│   ├── views.py          # Lógica das views
│   ├── forms.py          # Formulários
│   ├── admin.py          # Configuração do admin
│   ├── urls.py           # URLs do app
│   └── templates/        # Templates HTML
│       └── travels/
│           ├── base.html
│           ├── login.html
│           ├── register.html
│           ├── my_requests.html
│           ├── create_request.html
│           ├── request_detail.html
│           ├── bank_account.html
│           ├── dashboard.html
│           ├── all_requests.html
│           └── approve_request.html
├── media/                 # Uploads (notas fiscais)
├── static/               # Arquivos estáticos
├── manage.py             # Script de gerenciamento Django
├── requirements.txt      # Dependências Python
├── create_demo_users.py  # Script para criar usuários de teste
└── README.md            # Este arquivo
```

## Modelos de Dados

### UserProfile
Estende o modelo User do Django com:
- `user_type`: SOLICITANTE ou APROVADOR
- `cpf`: CPF do usuário
- `telefone`: Telefone de contato

### BankAccount
Dados bancários para reembolso:
- `banco`, `codigo_banco`, `agencia`, `conta`
- `tipo_conta`: CORRENTE ou POUPANCA
- `titular`, `cpf_titular`

### TravelRequest
Solicitação de viagem:
- Dados da viagem: destino, data, quilometragem
- Dados de combustível: valor do litro, valor total
- `nota_fiscal`: arquivo de comprovante
- `conta_bancaria`: referência à conta para reembolso
- `status`: PENDENTE, APROVADA, REJEITADA
- Dados de aprovação: aprovador, data, observações

## Segurança

- Autenticação obrigatória para todas as funcionalidades
- Separação de permissões por perfil (Solicitante/Aprovador)
- Validação de formulários
- Proteção CSRF em todos os formulários
- Upload seguro de arquivos com validação de tipo

## Personalização

### Alterar Perfil de Usuário

Para alterar um usuário de Solicitante para Aprovador (ou vice-versa):

1. Acesse o painel admin: http://127.0.0.1:8000/admin
2. Vá em "Usuários"
3. Selecione o usuário
4. Na seção "Perfil", altere o "Tipo de usuário"
5. Salve

### Configurar para Produção

1. Altere `DEBUG = False` em `settings.py`
2. Configure `ALLOWED_HOSTS` com seu domínio
3. Use PostgreSQL ou MySQL ao invés de SQLite
4. Configure variáveis de ambiente para SECRET_KEY
5. Configure servidor de arquivos estáticos (nginx, WhiteNoise)
6. Use servidor WSGI como Gunicorn

## Suporte e Contribuições

Para reportar bugs ou sugerir melhorias, abra uma issue no repositório do projeto.

## Licença

Este projeto foi desenvolvido para fins educacionais e empresariais.

## Autor

Sistema desenvolvido com Python/Django para gerenciamento de viagens e reembolsos.

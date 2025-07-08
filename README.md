# Sistema de Cadastro de Alunos - Cloudflare D1

Sistema de cadastro de alunos adaptado para usar Cloudflare D1 como banco de dados.

## Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Configurações do Cloudflare D1
CLOUDFLARE_ACCOUNT_ID=seu-account-id
CLOUDFLARE_DATABASE_ID=seu-database-id
CLOUDFLARE_API_TOKEN=seu-api-token

# Configurações do Flask
SECRET_KEY=sua-chave-secreta-super-segura

# Desenvolvimento local (usar SQLite)
USE_LOCAL_DB=True
```

### 2. Configuração do Cloudflare D1

#### Criando o banco D1:

```bash
# Instalar Wrangler CLI
npm install -g wrangler

# Login no Cloudflare
wrangler login

# Criar banco D1
wrangler d1 create cadastro-alunos
```

#### Criando as tabelas:

```bash
# Executar SQL para criar tabelas
wrangler d1 execute cadastro-alunos --command="
CREATE TABLE IF NOT EXISTS turmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    nascimento DATE NOT NULL,
    cpf TEXT UNIQUE NOT NULL,
    rg TEXT NOT NULL,
    celular TEXT NOT NULL,
    cep TEXT NOT NULL,
    graduacao TEXT NOT NULL,
    turma TEXT NOT NULL,
    foto TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (turma) REFERENCES turmas (nome)
);"
```

### 3. Obter credenciais

- **Account ID**: Encontre no dashboard do Cloudflare
- **Database ID**: Obtido após criar o banco D1
- **API Token**: Crie um token com permissões para D1

### 4. Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python app.py
```

## Desenvolvimento Local

Para desenvolvimento, o sistema usa SQLite local por padrão (`USE_LOCAL_DB=True`). O banco será criado automaticamente como `cadastro_alunos.db`.

## Deploy para Produção

Para usar em produção com Cloudflare D1:

1. Configure `USE_LOCAL_DB=False`
2. Configure todas as variáveis do Cloudflare
3. Certifique-se de que as tabelas foram criadas no D1

## Funcionalidades

- ✅ Cadastro de turmas
- ✅ Cadastro de alunos por turma
- ✅ Edição de alunos
- ✅ Exclusão de alunos
- ✅ Upload de fotos
- ✅ Exportação para Excel
- ✅ Contadores de turmas e alunos
- ✅ Interface responsiva
- ✅ Combobox de graduação com faixas coloridas

## Estrutura do Banco

### Tabela `turmas`
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `nome` (TEXT, UNIQUE, NOT NULL)
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### Tabela `alunos`
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `nome` (TEXT, NOT NULL)
- `nascimento` (DATE, NOT NULL)
- `cpf` (TEXT, UNIQUE, NOT NULL)
- `rg` (TEXT, NOT NULL)
- `celular` (TEXT, NOT NULL)
- `cep` (TEXT, NOT NULL)
- `graduacao` (TEXT, NOT NULL)
- `turma` (TEXT, NOT NULL, FK)
- `foto` (TEXT)
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

## Migração do MongoDB

O sistema foi migrado do MongoDB para Cloudflare D1/SQLite. As principais mudanças:

- Substituição do PyMongo pelo DatabaseManager customizado
- Criação de esquema SQL estruturado
- Abstração para funcionar tanto local (SQLite) quanto em produção (D1)
- Manutenção de todas as funcionalidades existentes

## Login

- **Usuário**: admin
- **Senha**: 1234
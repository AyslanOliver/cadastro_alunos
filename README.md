# 🎓 Sistema de Cadastro de Alunos

Sistema completo de cadastro de alunos com integração Cloudflare D1 (banco de dados) e Cloudflare R2 (armazenamento de imagens).

## Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Configurações do Cloudflare D1 (Banco de Dados)
CLOUDFLARE_ACCOUNT_ID=seu-account-id
CLOUDFLARE_DATABASE_ID=seu-database-id
CLOUDFLARE_API_TOKEN=seu-api-token

# Configurações do Cloudflare R2 (Armazenamento de Imagens)
CLOUDFLARE_R2_ACCESS_KEY_ID=seu-access-key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=sua-secret-key
CLOUDFLARE_R2_BUCKET_NAME=seu-bucket
CLOUDFLARE_R2_ENDPOINT_URL=https://seu-account-id.r2.cloudflarestorage.com
CLOUDFLARE_R2_PUBLIC_URL=https://pub-xxxxxxxxx.r2.dev

# Configurações do Flask
SECRET_KEY=sua-chave-secreta-super-segura

# Configurações de Ambiente
USE_LOCAL_DB=True          # False para produção
USE_CLOUDFLARE_R2=False    # True para produção
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

## 🚀 Deploy para Produção

### Deploy no Render

Para fazer deploy no Render, consulte o guia completo: **[DEPLOY_RENDER.md](DEPLOY_RENDER.md)**

**Resumo rápido:**
1. Configure todas as variáveis de ambiente no Render
2. Use `USE_LOCAL_DB=False` e `USE_CLOUDFLARE_R2=True`
3. Start Command: `gunicorn app:app`
4. Build Command: `pip install -r requirements.txt`

### Configuração para Produção

```env
# Produção
USE_LOCAL_DB=False
USE_CLOUDFLARE_R2=True
FLASK_ENV=production
```

## ✨ Funcionalidades

- ✅ **Cadastro de turmas** - Criação e gerenciamento de turmas
- ✅ **Cadastro de alunos** - Cadastro completo por turma
- ✅ **Edição de alunos** - Atualização de dados e fotos
- ✅ **Exclusão de alunos** - Remoção com limpeza de arquivos
- ✅ **Upload de fotos** - Cloudflare R2 ou armazenamento local
- ✅ **Exportação para Excel** - Relatórios com fotos incluídas
- ✅ **Contadores dinâmicos** - Estatísticas de turmas e alunos
- ✅ **Interface responsiva** - Design moderno e mobile-friendly
- ✅ **Validação de dados** - CPF, celular, CEP e outros campos
- ✅ **Sistema de login** - Controle de acesso
- ✅ **Graduação colorida** - Combobox com faixas por graduação

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

## 🔐 Login

- **Usuário**: admin
- **Senha**: 1234

## 📁 Arquivos Importantes

- `DEPLOY_RENDER.md` - Guia completo de deploy no Render
- `CLOUDFLARE_R2_SETUP.md` - Configuração do Cloudflare R2
- `.env.example` - Exemplo de variáveis de ambiente
- `.gitignore` - Arquivos ignorados pelo Git

## 🛠️ Tecnologias

- **Backend**: Flask (Python)
- **Banco de Dados**: Cloudflare D1 / SQLite
- **Armazenamento**: Cloudflare R2
- **Deploy**: Render
- **Frontend**: HTML, CSS, JavaScript
- **Servidor**: Gunicorn (produção)
# 🚀 Deploy da Aplicação no Render

Este guia mostra como fazer o deploy da aplicação de cadastro de alunos no Render.

## 📋 Pré-requisitos

✅ **Arquivos já configurados:**
- `requirements.txt` - Atualizado com gunicorn
- `.env` - Configurações do Cloudflare R2 e D1
- Aplicação Flask funcionando localmente

## 🔧 Preparação para Deploy

### 1. Verificar Arquivos Necessários

Certifique-se de que os seguintes arquivos estão no repositório:

```
cadastro_alunos/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências (com gunicorn)
├── .env.example          # Exemplo de variáveis de ambiente
├── database.py           # Gerenciador de banco
├── cloudflare_r2.py      # Upload de imagens
├── config.py             # Configurações
├── static/               # Arquivos estáticos
├── templates/            # Templates HTML
└── README.md             # Documentação
```

### 2. Configurar Variáveis de Ambiente

**⚠️ IMPORTANTE:** Não faça commit do arquivo `.env` com dados sensíveis!

No Render, você configurará as seguintes variáveis:

```env
# Cloudflare R2
CLOUDFLARE_R2_ACCESS_KEY_ID=seu_access_key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=sua_secret_key
CLOUDFLARE_R2_BUCKET_NAME=seu_bucket
CLOUDFLARE_R2_ENDPOINT_URL=https://seu_account_id.r2.cloudflarestorage.com
CLOUDFLARE_R2_PUBLIC_URL=https://pub-xxxxxxxxx.r2.dev

# Cloudflare D1
CLOUDFLARE_D1_DATABASE_ID=seu_database_id
CLOUDFLARE_D1_API_TOKEN=seu_api_token
CLOUDFLARE_ACCOUNT_ID=seu_account_id

# Configurações
USE_CLOUDFLARE_R2=True
USE_LOCAL_DB=False
FLASK_ENV=production
```

## 🌐 Deploy no Render

### Passo 1: Preparar Repositório

1. **Criar repositório no GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/seu-usuario/cadastro-alunos.git
   git push -u origin main
   ```

2. **Criar arquivo `.gitignore`:**
   ```
   .env
   __pycache__/
   *.pyc
   *.pyo
   *.pyd
   .Python
   env/
   venv/
   .venv/
   static/uploads/*
   !static/uploads/.gitkeep
   ```

### Passo 2: Configurar no Render

1. **Acessar o Render Dashboard:**
   - Vá para [render.com](https://render.com)
   - Faça login ou crie uma conta

2. **Criar Web Service:**
   - Clique em "New" → "Web Service"
   - Conecte seu repositório GitHub
   - Selecione o repositório da aplicação

3. **Configurações do Deploy:**
   ```
   Name: cadastro-alunos
   Language: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   ```

4. **Configurar Variáveis de Ambiente:**
   - Na seção "Environment Variables"
   - Adicione todas as variáveis listadas acima
   - **NÃO** inclua `FLASK_ENV=development`

5. **Configurações Avançadas:**
   ```
   Python Version: 3.11.x (ou sua versão)
   Plan: Free (para testes)
   Auto-Deploy: Yes
   ```

### Passo 3: Deploy

1. **Iniciar Deploy:**
   - Clique em "Create Web Service"
   - Aguarde o build completar (5-10 minutos)

2. **Verificar Logs:**
   - Monitore os logs durante o build
   - Verifique se não há erros

3. **Testar Aplicação:**
   - Acesse a URL fornecida pelo Render
   - Teste o cadastro de alunos
   - Verifique upload de fotos

## 🔍 Troubleshooting

### Problemas Comuns

**1. Erro de Build:**
```bash
# Verificar requirements.txt
# Certificar que todas as dependências estão listadas
```

**2. Erro de Start Command:**
```bash
# Verificar se o arquivo principal é app.py
# Start Command deve ser: gunicorn app:app
```

**3. Variáveis de Ambiente:**
```bash
# Verificar se todas as variáveis estão configuradas
# Especialmente as do Cloudflare R2 e D1
```

**4. Erro de Conexão com Cloudflare:**
```bash
# Verificar credenciais do R2 e D1
# Testar URLs públicas
```

### Logs Úteis

```bash
# Ver logs em tempo real no Render Dashboard
# Seção "Logs" do seu Web Service
```

## 📱 Configurações de Produção

### Otimizações

1. **Gunicorn Workers:**
   ```bash
   # Para melhor performance, configure workers
   Start Command: gunicorn --workers 2 --threads 4 app:app
   ```

2. **Timeout:**
   ```bash
   # Para uploads grandes
   Start Command: gunicorn --timeout 120 app:app
   ```

3. **Bind Port:**
   ```bash
   # Render configura automaticamente a porta
   # Não é necessário especificar --bind
   ```

## 🔒 Segurança

### Checklist de Segurança

- ✅ Arquivo `.env` não commitado
- ✅ Variáveis sensíveis no Render Environment
- ✅ `FLASK_ENV=production` (ou não definido)
- ✅ Debug mode desabilitado
- ✅ Credenciais do Cloudflare seguras

## 🎉 Próximos Passos

1. **Domínio Personalizado:**
   - Configure um domínio próprio no Render
   - Adicione certificado SSL automático

2. **Monitoramento:**
   - Configure alertas de uptime
   - Monitore performance

3. **Backup:**
   - Configure backup do Cloudflare D1
   - Backup das imagens no R2

4. **Escalabilidade:**
   - Considere upgrade para plano pago
   - Configure auto-scaling

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs no Render Dashboard
2. Confirme as variáveis de ambiente
3. Teste a aplicação localmente primeiro
4. Consulte a documentação do Render

**URL da aplicação após deploy:** `https://seu-app-name.onrender.com`
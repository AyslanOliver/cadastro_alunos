# Troubleshooting - Problemas no Render

## Problema: Turmas não estão sendo salvas no banco de dados

### Sintomas
- A aplicação funciona localmente
- No Render, ao tentar criar uma turma, ela não é salva no Cloudflare D1
- Possíveis timeouts ou erros de conexão

### Possíveis Causas e Soluções

#### 1. Problemas de Conectividade/Timeout

**Causa**: O Render pode ter limitações de rede ou timeouts mais restritivos.

**Solução**:
- Adicione a variável de ambiente `DEBUG_D1=true` no Render para ver logs detalhados
- Verifique os logs do Render para identificar erros específicos

#### 2. Configurações de Variáveis de Ambiente

**Verificar no Render**:
```
CLOUDFLARE_ACCOUNT_ID=c0c527df17c1d65d2ca35df56b1f0a71
CLOUDFLARE_DATABASE_ID=9a3795aa-7ddb-4245-b58d-2d150595d4e1
CLOUDFLARE_API_TOKEN=L740zq8B4WI05C8IxGorxwAiWAuCfu6Kt5j03fUK
USE_LOCAL_DB=False
USE_CLOUDFLARE_R2=True
SECRET_KEY=sua-chave-secreta-segura
DEBUG_D1=true
```

#### 3. Token da API Cloudflare

**Verificação**:
1. Acesse o [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Verifique se o token `L740zq8B4WI05C8IxGorxwAiWAuCfu6Kt5j03fUK` ainda está ativo
3. Confirme as permissões:
   - `Cloudflare D1:Edit`
   - `Account:Read`
   - Recursos: `Include - All accounts`

#### 4. Configuração do Banco D1

**Verificar estrutura das tabelas**:
```sql
-- Tabela de turmas
CREATE TABLE IF NOT EXISTS turmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de alunos
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
);
```

#### 5. Teste Manual da API

**Comando para testar no terminal do Render**:
```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/c0c527df17c1d65d2ca35df56b1f0a71/d1/database/9a3795aa-7ddb-4245-b58d-2d150595d4e1/query" \
  -H "Authorization: Bearer L740zq8B4WI05C8IxGorxwAiWAuCfu6Kt5j03fUK" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM turmas"}'
```

### Soluções Alternativas

#### Opção 1: Usar PostgreSQL do Render

Se os problemas persistirem, considere migrar para PostgreSQL:

1. No Render, crie um banco PostgreSQL
2. Atualize as configurações:
   ```
   USE_LOCAL_DB=False
   DATABASE_URL=postgresql://...
   ```
3. Modifique `database.py` para suportar PostgreSQL

#### Opção 2: Implementar Retry Logic

O código já inclui retry logic com 3 tentativas. Para aumentar:

```python
# Em database.py, linha ~102
max_retries = 5  # Aumentar de 3 para 5
```

### Como Debuggar

1. **Ativar logs detalhados**:
   - Adicione `DEBUG_D1=true` nas variáveis de ambiente do Render

2. **Verificar logs do Render**:
   - Acesse o dashboard do Render
   - Vá em "Logs" do seu serviço
   - Procure por mensagens `[D1 DEBUG]` ou `[D1 WARNING]`

3. **Testar localmente com as mesmas configurações**:
   ```bash
   set DEBUG_D1=true
   set USE_LOCAL_DB=False
   python test_d1_connection.py
   ```

### Contato para Suporte

Se o problema persistir:
1. Colete os logs do Render com `DEBUG_D1=true`
2. Teste a API do Cloudflare manualmente
3. Verifique se há mudanças nas configurações do Cloudflare

---

**Última atualização**: Janeiro 2025
**Versão**: 1.0
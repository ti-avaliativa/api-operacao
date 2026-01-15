
# API Operação - Avaliação Rede

Esta API foi configurada para operar na rota `https://api.operacao.avaliarede.com.br/api_operacao/` em **produção**.

## URLs da API

### 🌐 Produção
```
https://api.operacao.avaliarede.com.br/api_operacao/
```

### 🏠 Desenvolvimento Local
```
http://localhost:8000/
http://localhost:8000/docs  (documentação)
```

### Exemplos de Endpoints
```
https://api.operacao.avaliarede.com.br/api_operacao/
https://api.operacao.avaliarede.com.br/api_operacao/{db}
https://api.operacao.avaliarede.com.br/api_operacao/{db}/associar/professor/{pid}/turmas/{tids}
```

## Docker Commands

### Para parar o container
```bash
docker stop operacao_api
```

### Para remover o container
```bash
docker rm operacao_api
```

### Para remover a imagem
```bash
docker rmi operacao_api --force
```

### Para criar a imagem
```bash
docker build -t operacao_api .
```

### Para logar no ECR (lembre de configurar as credenciais em ~/.aws/config)
```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 895525808331.dkr.ecr.us-west-2.amazonaws.com
```

### Para tagear a imagem
```bash
docker tag operacao_api:latest 895525808331.dkr.ecr.us-west-2.amazonaws.com/avaliativa:operacao_api
```

### Para subir image no ECR
```bash
docker push 895525808331.dkr.ecr.us-west-2.amazonaws.com/avaliativa:operacao_api
```

## Alterações Realizadas

### 1. Configurações Principais
- **Nome da API**: Alterado de `escanemanto_api` para `operacao_api`
- **Root Path**: Alterado de `/apiavrede` para `/api_operacao`
- **Arquivo principal**: `operacao_api.py` (já estava correto)

### 2. Docker Configuration
- **Dockerfile**: Corrigido para referenciar `app.operacao_api:app`
- **Container Name**: Alterado para `operacao_api`
- **Image**: `895525808331.dkr.ecr.us-west-2.amazonaws.com/avaliativa:operacao_api`

### 3. AWS ECS Task Definition
- **Task Definition**: `operacao-api-task-def`
- **Log Group**: `/ecs/operacao-api-task-def`
- **Port Mapping**: `operacao_api-8000-tcp`

## Configuração de Ambiente

### Variáveis de Ambiente
- `API_KEY`: Chave de autenticação da API (já configurada no Dockerfile)

### Configurações de Banco
- Host: `mysql`
- Port: `3306`
- User: `avaliare_user`
- Password: `avaliare_pass`
- Database: Definido dinamicamente via URL path

## 🎯 Refatoração SOLID (Nova Arquitetura)

### ✨ O que mudou?

A aplicação foi refatorada seguindo os princípios **SOLID** para melhor manutenibilidade e escalabilidade.

### 📁 Nova Estrutura

```
app/
├── core/                      # Infraestrutura
│   ├── config.py             # Configurações centralizadas
│   ├── database.py           # Pool de conexões MySQL
│   ├── cache.py              # Sistema de cache
│   └── security.py           # Middlewares de segurança
│
├── routers/                   # Endpoints da API
│   ├── estrutura.py          # Importação de estrutura
│   ├── alunos.py             # Importação de alunos
│   └── sistema.py            # Sistema e health checks
│
├── services/                  # Lógica de negócio
│   ├── estrutura_service.py  # Serviço de estrutura
│   └── alunos_service.py     # Serviço de alunos
│
├── utils/                     # Utilitários
│   ├── text_utils.py         # Manipulação de texto
│   └── csv_processor.py      # Processamento de CSV
│
├── main.py                    # Aplicação principal (NOVO)
└── operacao_api.py           # Arquivo original (mantido)
```

### 🚀 Como usar a nova arquitetura

#### Opção 1: Usar main.py (Recomendado)

```python
# No Dockerfile ou servidor WSGI/ASGI
from app.main import app
```

#### Opção 2: Manter operacao_api.py

O arquivo original continua funcionando normalmente.

### 📚 Documentação da Refatoração

- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Resumo completo
- **[app/REFACTORING.md](app/REFACTORING.md)** - Visão geral detalhada
- **[app/MIGRATION_GUIDE.md](app/MIGRATION_GUIDE.md)** - Guia de migração
- **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - Exemplos de uso
- **[VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)** - Checklist

### 🎯 Benefícios

- ✅ Código organizado por responsabilidade (SOLID)
- ✅ Fácil manutenção e testes
- ✅ Escalabilidade melhorada
- ✅ Documentação completa
- ✅ Todos os endpoints mantidos

### 📊 Endpoints Disponíveis

#### Importação de Estrutura
- `POST /import/completo` - Importação de escola/série/turma
- `GET /import/info` - Informações sobre formato

#### Importação de Alunos (Multi-step)
- `POST /import/alunos/step1` - Upload e validação
- `POST /import/alunos/step2` - Mapeamento de colunas
- `POST /import/alunos/step3` - Detecção de conflitos
- `POST /import/alunos/step4` - Resolução de conflitos
- `POST /import/alunos/step5` - Importação final
- `GET /import/alunos/status` - Status da importação

#### Sistema
- `GET /` - Root
- `GET /{db}` - Validação de database
- `GET /test` - Teste de funcionamento
- `GET /security/blocked-ips` - IPs bloqueados
- `GET /security/stats` - Estatísticas de segurança






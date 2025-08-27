# VectorLess - Docker Setup

Este documento contém instruções para executar o projeto VectorLess usando Docker.

## 📋 Pré-requisitos

- Docker instalado (versão 20.10 ou superior)
- Docker Compose instalado (versão 2.0 ou superior)
- Chave da API da OpenAI

## 🚀 Configuração Inicial

### 1. Configure as variáveis de ambiente

Copie o arquivo de exemplo e configure suas variáveis:

```bash
# Copie o arquivo de exemplo
cp env.example .env

# Edite o arquivo .env e adicione sua chave da OpenAI
nano .env
```

**Variáveis obrigatórias:**
- `OPENAI_API_KEY`: Sua chave da API da OpenAI

### 2. Estrutura dos arquivos criados

```
vectorless/
├── Dockerfile                 # Configuração do Docker
├── docker-compose.yml         # Orquestração para produção
├── docker-compose.dev.yml     # Orquestração para desenvolvimento
├── .dockerignore              # Arquivos ignorados no build
├── env.example                # Exemplo de variáveis de ambiente
├── nginx.conf                 # Configuração do proxy reverso
└── backend/
    └── env_example.txt        # Exemplo de variáveis para o backend
```

## 🏃‍♂️ Executando o Projeto

### Opção 1: Desenvolvimento (Recomendado para desenvolvimento)

```bash
# Execute com hot-reload
docker-compose -f docker-compose.dev.yml up --build

# Para executar em background
docker-compose -f docker-compose.dev.yml up --build -d
```

### Opção 2: Produção

```bash
# Execute em modo produção
docker-compose up --build

# Para executar em background
docker-compose up --build -d
```

### Opção 3: Produção com Nginx (Proxy Reverso)

```bash
# Execute com Nginx
docker-compose --profile production up --build

# Para executar em background
docker-compose --profile production up --build -d
```

## 🌐 Acessando a Aplicação

Após executar os comandos, acesse:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Com Nginx**: http://localhost:80 (ou http://localhost)

## 🔧 Comandos Úteis

### Ver logs dos serviços
```bash
# Todos os serviços
docker-compose logs

# Serviço específico
docker-compose logs frontend
docker-compose logs backend

# Logs em tempo real
docker-compose logs -f
```

### Parar os serviços
```bash
# Para desenvolvimento
docker-compose -f docker-compose.dev.yml down

# Para produção
docker-compose down

# Para parar e remover volumes
docker-compose down -v
```

### Rebuild das imagens
```bash
# Para desenvolvimento
docker-compose -f docker-compose.dev.yml up --build

# Para produção
docker-compose up --build
```

### Acessar o container
```bash
# Frontend
docker-compose exec frontend sh

# Backend
docker-compose exec backend bash
```

## 📁 Estrutura dos Volumes

- `./uploads`: Diretório para uploads de arquivos PDF
- `./backend`: Código fonte do backend (apenas desenvolvimento)
- `.`: Código fonte completo (apenas desenvolvimento)

## 🔒 Configurações de Segurança

### Variáveis de Ambiente Importantes

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Portas
FRONTEND_PORT=3000
BACKEND_PORT=8000
NGINX_PORT=80

# URLs
BACKEND_URL=http://localhost:8000

# Limites
MAX_FILE_SIZE=10485760  # 10MB
MAX_FILES_PER_UPLOAD=100
```

## 🐛 Solução de Problemas

### Problema: Container não inicia
```bash
# Verifique os logs
docker-compose logs

# Verifique se as portas estão disponíveis
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
```

### Problema: Erro de permissão
```bash
# No Windows, certifique-se de que o Docker Desktop tem acesso aos arquivos
# No Linux/Mac, ajuste as permissões
chmod -R 755 .
```

### Problema: Variáveis de ambiente não carregadas
```bash
# Verifique se o arquivo .env existe
ls -la .env

# Verifique o conteúdo
cat .env
```

### Problema: OpenAI API não funciona
```bash
# Verifique se a chave está correta
echo $OPENAI_API_KEY

# Teste a API diretamente
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

## 🚀 Deploy em Produção

### 1. Configure as variáveis para produção
```bash
# Edite o arquivo .env
NODE_ENV=production
NGINX_PORT=80
```

### 2. Execute com Nginx
```bash
docker-compose --profile production up --build -d
```

### 3. Configure o domínio (opcional)
Edite o arquivo `nginx.conf` e altere `server_name localhost` para seu domínio.

## 📊 Monitoramento

### Health Check
```bash
# Frontend
curl http://localhost:3000

# Backend
curl http://localhost:8000/health

# Com Nginx
curl http://localhost/health
```

### Logs estruturados
Os logs são configurados para facilitar o monitoramento em produção.

## 🔄 Atualizações

Para atualizar o projeto:

```bash
# Pare os containers
docker-compose down

# Pull das últimas mudanças
git pull

# Rebuild e execute
docker-compose up --build
```

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `docker-compose logs`
2. Confirme as variáveis de ambiente
3. Verifique se as portas estão disponíveis
4. Consulte a documentação do Docker

---

**Nota**: Este setup Docker foi otimizado para desenvolvimento e produção. Para ambientes corporativos, considere adicionar configurações de segurança adicionais.

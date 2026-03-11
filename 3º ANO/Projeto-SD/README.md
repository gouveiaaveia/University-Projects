# Googol - Motor de Pesquisa Distribuído

Motor de pesquisa distribuído desenvolvido em Python, utilizando **gRPC** para comunicação entre componentes e **FastAPI** para a interface web.

---

## 📦 Requisitos

- **Python 3.10+**
- **pip** (gestor de pacotes Python)

---

## ⚙️ Instalação

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Criar o ficheiro `.env` na **raiz do projeto** com o seguinte conteúdo:

```env
# Endereço do Gateway
GATEWAY_HOST=localhost
GATEWAY_PORT=8183

# IP do servidor (para ambiente distribuído)
SERVER_IP=localhost

# Endereço que os Barrels anunciam ao Gateway
BARREL_ADVERTISE_HOST=localhost

# Chaves API para IA (opcional)
GROQ_API_KEY=sua_chave_groq
GEMINI_API_KEY=sua_chave_gemini
```

> **Nota:** As chaves de IA são opcionais. Sem elas, o assistente IA usa Ollama local como fallback.

### 3. (Opcional) Gerar Certificados HTTPS

```bash
cd web
python generate_certs.py
```

---

## 🚀 Execução

### Ordem de Inicialização

Os componentes devem ser iniciados na seguinte ordem:

```
1. Gateway  →  2. Barrel(s)  →  3. Downloader(s)  →  4. Web App
```

---

### Terminal 1 - Gateway

O Gateway é o coordenador central que gere a fila de URLs e o load balancing.

```bash
cd search
python gateaway.py
```

Inicia na porta **8183** por defeito.

---

### Terminal 2 - Barrel

O Barrel mantém o índice invertido e responde a pesquisas.

```bash
cd search
python barrel.py 8184
```

Podes iniciar **múltiplos Barrels** em portas diferentes:

```bash
python barrel.py 8185
python barrel.py 8186
```

Os Barrels sincronizam automaticamente o estado entre si.

---

### Terminal 3 - Downloader

O Downloader faz crawling de páginas web e indexa o conteúdo.

```bash
cd search
python downloader.py
```

Podes iniciar **múltiplos Downloaders** para processar URLs em paralelo.

---

### Terminal 4 - Web App

```bash
cd web
python app.py
```

A aplicação web fica disponível em:
- **HTTP:** http://localhost:8000
- **HTTPS:** https://localhost:8000 (se os certificados existirem)

---

## 🖥️ Funcionalidades da Interface Web

| URL | Descrição |
|-----|-----------|
| `/` | Página inicial com barra de pesquisa |
| `/search?q=termo` | Resultados de pesquisa com paginação |
| `/index-link` | Indexar URLs manualmente |
| `/links-to?url=...` | Ver páginas que apontam para um URL |
| `/stats` | Estatísticas em tempo real (WebSocket) |
| `/ai-mode` | Chat com assistente IA |

### Funcionalidades Especiais

- **Resumo IA**: Na página de resultados, aparece um resumo gerado por IA sobre a pesquisa
- **Indexar Hacker News**: Botão para indexar as top 50 notícias do HN relacionadas com a pesquisa
- **Estatísticas em Tempo Real**: Top 10 pesquisas e estado dos Barrels via WebSocket

---

## 📁 Estrutura do Projeto

```
SD-Project/
├── .env                      # Configuração (criar manualmente)
├── .gitignore
├── requirements.txt          # Dependências Python
├── README.md
│
├── search/                   # Backend de pesquisa (gRPC)
│   ├── gateaway.py          # Gateway - Coordenador central
│   ├── barrel.py            # Barrel - Índice invertido
│   ├── downloader.py        # Downloader - Web crawler
│   ├── user.py              # Cliente CLI (para testes)
│   ├── index_pb2.py         # Código gRPC gerado
│   ├── index_pb2_grpc.py    # Código gRPC gerado
│   └── protos/
│       ├── index.proto      # Definição do serviço gRPC
│       └── generate-gRPC-code.sh
│
└── web/                      # Frontend (FastAPI + MVC)
    ├── app.py               # Ponto de entrada da aplicação
    ├── generate_certs.py    # Gerador de certificados HTTPS
    │
    ├── controllers/         # CONTROLLER - Rotas HTTP
    │   ├── home_controller.py
    │   ├── search_controller.py
    │   ├── index_controller.py
    │   ├── stats_controller.py
    │   ├── ai_controller.py
    │   └── api_controller.py
    │
    ├── models/              # MODEL - Estruturas de dados
    │   ├── search.py
    │   ├── statistics.py
    │   └── ai.py
    │
    ├── services/            # Lógica de negócio (clientes gRPC)
    │   ├── search_service.py
    │   ├── index_service.py
    │   ├── stats_service.py
    │   └── ai_service.py
    │
    └── templates/           # VIEW - HTML/CSS (Jinja2)
        ├── HomePage/
        ├── SearchPage/
        ├── AIpage/
        ├── IndexLinkPage/
        ├── LinksToPage/
        └── StatsPage/
```

---

## 🔧 Arquitetura

### Comunicação gRPC

- **Gateway ↔ Barrel**: Registo de serviços, heartbeats, pesquisas
- **Downloader → Gateway**: Obter URLs da fila
- **Downloader → Barrels**: Indexar páginas (multicast)

### Padrões Implementados

- **Service Discovery**: Barrels registam-se dinamicamente no Gateway
- **Load Balancing**: Round-robin para distribuir pesquisas
- **Replicação**: Escrita multicast para todos os Barrels
- **Failover**: Se um Barrel falha, tenta outro automaticamente
- **Persistência**: Checkpoint (pickle) + AOF (log) para recuperação
- **Cache**: TTL cache para resultados de pesquisa frequentes

---

## 🔄 Regenerar Código gRPC

Se modificares o ficheiro `index.proto`:

```bash
cd search/protos
chmod +x generate-gRPC-code.sh
./generate-gRPC-code.sh
```

Ou manualmente:

```bash
cd search/protos
python -m grpc_tools.protoc -I. --python_out=.. --grpc_python_out=.. index.proto
```

---

## 🧪 Testar o Sistema

1. Inicia todos os componentes (Gateway, Barrel, Downloader, Web)
2. Acede a http://localhost:8000
3. Vai a "Index Links" e adiciona um URL (ex: `https://pt.wikipedia.org/wiki/Portugal`)
4. Aguarda alguns segundos para o Downloader processar
5. Pesquisa por palavras que existam na página indexada

---

## ❓ Troubleshooting

### "Gateway indisponível"
- Verifica se o Gateway está a correr na porta 8183
- Verifica as variáveis de ambiente no `.env`

### "Nenhum Barrel ativo"
- Inicia pelo menos um Barrel antes do Downloader
- Verifica se o Barrel consegue contactar o Gateway

### IA não funciona
- Verifica se as chaves API estão configuradas no `.env`
- Alternativa: instala Ollama localmente

```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
ollama serve
```

```powershell
# Windows - Descarregar de https://ollama.com/download
ollama pull llama3.2
ollama serve
```

---

## 👥 Autores

Projeto desenvolvido para a UC de Sistemas Distribuídos.

# ⚽ Football Analytics Pipeline

> Pipeline de dados de futebol com ingestão automatizada, armazenamento em arquitetura medalhão e serving via API REST e dashboard interativo.

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-336791?style=flat&logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-2.7-EA4B71?style=flat&logo=n8n&logoColor=white)

---

## 📋 Sobre o projeto

Pipeline completo de Data Engineering aplicado a dados de futebol. O sistema coleta automaticamente estatísticas de partidas, classificações e times das principais ligas do mundo, processa os dados em camadas (Bronze → Silver → Gold) e os disponibiliza via API REST e dashboard visual.

**Ligas cobertas atualmente:**
- 🇧🇷 Brasileirão Série A
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League
- 🌍 UEFA Champions League

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    FONTES DE DADOS                       │
│         football-data.org  •  API-Football               │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  ORQUESTRAÇÃO (n8n)                      │
│     Cron diário 8h  •  Workflows encadeados              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   ETL (Python)                           │
│   Collector  →  Transformer  →  Loader                   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL — Arquitetura Medalhão           │
│   bronze (raw)  →  silver (clean)  →  gold (analytics)  │
└──────────┬────────────────────────────┬─────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────┐         ┌──────────────────────────┐
│   FastAPI        │         │   Streamlit Dashboard     │
│   REST API       │         │   Visualização interativa │
└──────────────────┘         └──────────────────────────┘
```

---

## 🛠️ Stack tecnológica

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| Linguagem | Python 3.10 | ETL, API e análise |
| Orquestração | n8n 2.7 | Agendamento e automação |
| Banco de dados | PostgreSQL 14 | Armazenamento estruturado |
| API | FastAPI | Serving REST com Swagger |
| Dashboard | Streamlit | Visualização interativa |
| Análise | Jupyter + Pandas | Exploração e insights |
| Infraestrutura | systemd + Docker | Serviços persistentes |

---

## 📁 Estrutura do projeto

```
football-analytics/
├── collector/
│   ├── api_football.py          # Coletor API-Football (ao vivo)
│   └── football_data.py         # Coletor football-data.org (histórico)
├── transformer/
│   └── football_data_transformer.py  # Limpeza e normalização
├── loader/
│   └── db_loader.py             # Upsert no PostgreSQL
├── api/
│   ├── main.py                  # FastAPI — endpoints de consulta
│   └── trigger.py               # FastAPI — trigger ETL via HTTP
├── dashboard/
│   └── app.py                   # Streamlit dashboard
├── notebooks/
│   └── 01_eda_partidas.ipynb    # Análise exploratória
├── run_etl.py                   # Script principal do pipeline
├── requirements.txt
└── .env                         # Variáveis de ambiente (não versionado)
```

---

## 🚀 Como executar

### Pré-requisitos

- Python 3.10+
- PostgreSQL 14+
- n8n (Docker)
- Chave da API: [football-data.org](https://www.football-data.org/client/register)

### 1. Clone o repositório

```bash
git clone https://github.com/Larbac0/football-analytics.git
cd football-analytics
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

```env
FOOTBALL_DATA_KEY=sua_chave_aqui
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4

DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_analytics
DB_USER=football_user
DB_PASSWORD=sua_senha_aqui
```

### 4. Crie o banco de dados

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE football_analytics WITH ENCODING 'UTF8' TEMPLATE=template0;
CREATE USER football_user WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE football_analytics TO football_user;
```

```bash
sudo -u postgres psql -d football_analytics < schema.sql
```

### 5. Execute o pipeline

```bash
python run_etl.py
```

### 6. Suba a API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 7. Suba o dashboard

```bash
streamlit run dashboard/app.py --server.port 8502
```

---

## 📊 Arquitetura de dados — Medalhão

### 🥉 Bronze (raw_data)
Dados brutos como vieram da API, sem nenhuma modificação. Garantia de rastreabilidade e reprocessamento.

| Tabela | Conteúdo |
|--------|----------|
| `raw_matches` | JSON completo de partidas por requisição |
| `raw_standings` | JSON completo de classificações |

### 🥈 Silver (processed)
Dados limpos, tipados e normalizados. Schema relacional estruturado.

| Tabela | Conteúdo |
|--------|----------|
| `competitions` | Ligas e competições |
| `teams` | Times com nome e país |
| `matches` | Partidas com placar e status |
| `standings` | Classificação por liga e temporada |

### 🥇 Gold (analytics)
Views prontas para consumo pela API e dashboard.

| View | Conteúdo |
|------|----------|
| `vw_standings_current` | Classificação atual por liga |
| `vw_recent_matches` | Partidas recentes com vencedor calculado |

---

## 🔌 API Endpoints

Documentação interativa disponível em `/docs` (Swagger UI).

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/ligas` | Lista todas as ligas cobertas |
| GET | `/ligas/{code}/classificacao` | Classificação de uma liga |
| GET | `/partidas/recentes` | Partidas recentes com filtro opcional |
| GET | `/partidas/{id}` | Detalhe de uma partida |
| GET | `/times` | Lista times com busca por nome |
| GET | `/times/{id}/historico` | Histórico de resultados de um time |
| POST | `/run-etl/all` | Dispara o pipeline completo |
| POST | `/run-etl/{competition}` | Dispara o pipeline de uma liga |

---

## 🤖 Automação com n8n

O n8n orquestra a execução automática do pipeline via chamadas HTTP ao endpoint `/run-etl/all`.

| Workflow | Frequência | Função |
|----------|-----------|--------|
| `daily_etl_football` | Todo dia às 8h | Coleta partidas e classificações das 3 ligas |

---

## 📈 Análises disponíveis

O notebook `01_eda_partidas.ipynb` cobre:

- Distribuição de gols por liga e por partida
- Vantagem do mandante — geral e por liga
- Gols pró vs contra por time no Brasileirão
- Insights automáticos com estatísticas descritivas

**Insights do período atual:**
- 🇧🇷 Brasileirão: 2.14 gols/partida
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League: 2.89 gols/partida
- 🌍 Champions League: 4.50 gols/partida
- 🏠 Mandante vence em 60.5% das partidas

---

## 🗺️ Roadmap

- [ ] Adicionar La Liga, Bundesliga, Serie A e Ligue 1
- [ ] Estatísticas de jogadores por partida
- [ ] Artilheiros por liga
- [ ] Histórico de temporadas anteriores
- [ ] Deploy na nuvem (Railway / Render)
- [ ] Integração com Microsoft Fabric (DP-700)
- [ ] Modelo de previsão de resultado com scikit-learn

---

## 👤 Autor

**Igor (Igão)** — [@Larbac0](https://github.com/Larbac0)

Projeto desenvolvido como parte do portfólio de transição para Data Engineering / Data Analysis.

---

*Dados fornecidos por [football-data.org](https://www.football-data.org)*

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
from run_etl import run

load_dotenv()

app = FastAPI(
    title="Football Analytics API",
    description="Estatísticas de futebol — Premier League, Brasileirão e Champions League",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    conn.set_client_encoding('UTF8')
    return conn

def query(sql: str, params=None):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

# ── Health ──────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}

# ── Trigger ETL ─────────────────────────────────────────

@app.post("/run-etl/all", tags=["ETL"])
def trigger_all(background_tasks: BackgroundTasks):
    for league in ["PL", "BSA", "CL"]:
        background_tasks.add_task(run, competition=league, days_back=7)
    return {"status": "started", "leagues": ["PL", "BSA", "CL"]}

@app.post("/run-etl/{competition}", tags=["ETL"])
def trigger_one(competition: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(run, competition=competition, days_back=7)
    return {"status": "started", "competition": competition}

# ── Ligas ────────────────────────────────────────────────

@app.get("/ligas", tags=["Ligas"])
def ligas():
    rows = query("SELECT code, name, country FROM silver.competitions ORDER BY name")
    return list(rows)

# ── Classificação ────────────────────────────────────────

@app.get("/ligas/{code}/classificacao", tags=["Ligas"])
def classificacao(code: str):
    rows = query("""
        SELECT position, team, played, won, draw, lost,
               goals_for, goals_against, goal_diff, points
        FROM gold.vw_standings_current
        WHERE competition_code = %s
    """, (code.upper(),))
    if not rows:
        raise HTTPException(status_code=404, detail=f"Liga '{code}' não encontrada")
    return list(rows)

# ── Partidas ─────────────────────────────────────────────

@app.get("/partidas/recentes", tags=["Partidas"])
def partidas_recentes(liga: str = None, limit: int = 20):
    if liga:
        rows = query("""
            SELECT id, competition_code, match_date, status,
                   home_team, away_team, home_score, away_score, winner
            FROM gold.vw_recent_matches
            WHERE competition_code = %s
            LIMIT %s
        """, (liga.upper(), limit))
    else:
        rows = query("""
            SELECT id, competition_code, match_date, status,
                   home_team, away_team, home_score, away_score, winner
            FROM gold.vw_recent_matches
            LIMIT %s
        """, (limit,))
    return list(rows)

@app.get("/partidas/{match_id}", tags=["Partidas"])
def partida_detalhe(match_id: int):
    rows = query("""
        SELECT m.id, m.competition_code, m.match_date, m.status,
               ht.name AS home_team, at.name AS away_team,
               m.home_score, m.away_score, m.stage, m.season
        FROM silver.matches m
        JOIN silver.teams ht ON ht.id = m.home_team_id
        JOIN silver.teams at ON at.id = m.away_team_id
        WHERE m.id = %s
    """, (match_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return dict(rows[0])

# ── Times ────────────────────────────────────────────────

@app.get("/times/{team_id}/historico", tags=["Times"])
def historico_time(team_id: int, limit: int = 10):
    rows = query("""
        SELECT m.id, m.competition_code, m.match_date, m.status,
               ht.name AS home_team, at.name AS away_team,
               m.home_score, m.away_score,
               CASE
                   WHEN m.home_team_id = %s AND m.home_score > m.away_score THEN 'V'
                   WHEN m.away_team_id = %s AND m.away_score > m.home_score THEN 'V'
                   WHEN m.home_score = m.away_score THEN 'E'
                   ELSE 'D'
               END AS resultado
        FROM silver.matches m
        JOIN silver.teams ht ON ht.id = m.home_team_id
        JOIN silver.teams at ON at.id = m.away_team_id
        WHERE (m.home_team_id = %s OR m.away_team_id = %s)
          AND m.status = 'FINISHED'
        ORDER BY m.match_date DESC
        LIMIT %s
    """, (team_id, team_id, team_id, team_id, limit))
    if not rows:
        raise HTTPException(status_code=404, detail="Time não encontrado ou sem partidas")
    return list(rows)

@app.get("/times", tags=["Times"])
def times(nome: str = None):
    if nome:
        rows = query("""
            SELECT id, name, short_name, country
            FROM silver.teams
            WHERE LOWER(name) LIKE %s
            ORDER BY name
        """, (f"%{nome.lower()}%",))
    else:
        rows = query("SELECT id, name, short_name, country FROM silver.teams ORDER BY name")
    return list(rows)

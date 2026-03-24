import psycopg2
import psycopg2.extras
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    conn.set_client_encoding('UTF8')
    return conn

def save_raw(source: str, competition: str, data_type: str, raw_data: dict):
    """
    Grava o JSON bruto na camada Bronze.
    data_type: 'matches' ou 'standings'
    """
    table = f"bronze.raw_{data_type}"
    sql = f"""
        INSERT INTO {table} (source, competition, raw_data)
        VALUES (%s, %s, %s)
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (source, competition, json.dumps(raw_data)))
        log.info(f"Bronze: gravado {data_type} de {competition} ({source})")
    finally:
        conn.close()

def upsert_competition(code: str, name: str, country: str = None):
    sql = """
        INSERT INTO silver.competitions (code, name, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            name    = EXCLUDED.name,
            country = EXCLUDED.country
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (code, name, country))
        log.info(f"Silver: competition upsert — {code}")
    finally:
        conn.close()

def upsert_team(team_id: int, name: str, short_name: str = None, country: str = None):
    sql = """
        INSERT INTO silver.teams (id, name, short_name, country)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name       = EXCLUDED.name,
            short_name = EXCLUDED.short_name,
            country    = EXCLUDED.country
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (team_id, name, short_name, country))
    finally:
        conn.close()

def upsert_match(match: dict):
    sql = """
        INSERT INTO silver.matches (
            id, competition_code, season, match_date, status,
            home_team_id, away_team_id, home_score, away_score, stage
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            status     = EXCLUDED.status,
            home_score = EXCLUDED.home_score,
            away_score = EXCLUDED.away_score,
            updated_at = NOW()
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    match["id"],
                    match["competition_code"],
                    match["season"],
                    match["match_date"],
                    match["status"],
                    match["home_team_id"],
                    match["away_team_id"],
                    match["home_score"],
                    match["away_score"],
                    match["stage"],
                ))
    finally:
        conn.close()

def upsert_standings(rows: list, competition: str, season: str):
    """
    Substitui a classificação atual de uma liga.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM silver.standings WHERE competition_code = %s AND season = %s",
                    (competition, season)
                )
                for row in rows:
                    cur.execute("""
                        INSERT INTO silver.standings (
                            competition_code, season, position, team_id,
                            played, won, draw, lost,
                            goals_for, goals_against, goal_diff, points
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        competition, season,
                        row["position"], row["team_id"],
                        row["played"], row["won"], row["draw"], row["lost"],
                        row["goals_for"], row["goals_against"],
                        row["goal_diff"], row["points"]
                    ))
        log.info(f"Silver: standings upsert — {competition} {season} ({len(rows)} times)")
    finally:
        conn.close()


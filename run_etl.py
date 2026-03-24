import logging
from datetime import date, timedelta
from collector.football_data import get_matches, get_standings, LEAGUES
from transformer.football_data_transformer import (
    transform_matches,
    transform_teams_from_matches,
    transform_teams_from_standings,
    transform_standings
)
from loader.db_loader import (
    save_raw,
    upsert_competition,
    upsert_team,
    upsert_match,
    upsert_standings
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

COMPETITION_NAMES = {
    "PL":  ("Premier League", "England"),
    "CL":  ("Champions League", "Europe"),
    "BSA": ("Brasileirão Série A", "Brazil"),
    "PD":  ("La Liga", "Spain"),
    "BL1": ("Bundesliga", "Germany"),
    "SA":  ("Serie A", "Italy"),
    "FL1": ("Ligue 1", "France"),
}

# Ligas com temporada = ano calendário (não split de verão europeu)
CALENDAR_YEAR_LEAGUES = {"BSA", "MLS", "APL"}

def run(competition: str = "PL", days_back: int = 7):
    hoje = date.today()
    date_from = (hoje - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to   = hoje.strftime("%Y-%m-%d")
    if competition in CALENDAR_YEAR_LEAGUES:
        season = str(hoje.year)
    else:
        season = str(hoje.year if hoje.month >= 7 else hoje.year - 1)

    log.info(f"Iniciando ETL — {competition} | {date_from} até {date_to}")

    # 1. Upsert competition
    name, country = COMPETITION_NAMES.get(competition, (competition, None))
    upsert_competition(competition, name, country)

    # 2. Coleta (Extract)
    log.info("Coletando partidas...")
    raw_matches = get_matches(competition, date_from, date_to)
    if not raw_matches:
        log.warning("Nenhuma partida retornada. Abortando.")
        return

    # 3. Grava Bronze
    save_raw("football-data.org", competition, "matches", {"matches": raw_matches})

    # 4. Transforma (Transform)
    teams    = transform_teams_from_matches(raw_matches)
    matches  = transform_matches(raw_matches, competition)

    # 5. Grava Silver (Load)
    log.info(f"Gravando {len(teams)} times e {len(matches)} partidas na Silver...")
    for team in teams:
        upsert_team(team["id"], team["name"], team["short_name"], team["country"])
    for match in matches:
        upsert_match(match)

    # 6. Classificação
    log.info("Coletando classificação...")
    raw_standings = get_standings(competition)
    if raw_standings:
        save_raw("football-data.org", competition, "standings", {"standings": raw_standings})
        # Garante que todos os times da classificação existem na Silver
        standing_teams = transform_teams_from_standings(raw_standings)
        for team in standing_teams:
            upsert_team(team["id"], team["name"], team["short_name"], team["country"])
        standings = transform_standings(raw_standings, competition, season)
        upsert_standings(standings, competition, season)

    log.info(f"ETL concluído — {competition}")

if __name__ == "__main__":
    for league in ["PL", "BSA", "CL"]:
        run(competition=league, days_back=7)

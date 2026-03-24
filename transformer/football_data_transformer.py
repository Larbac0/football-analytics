import logging

log = logging.getLogger(__name__)

def transform_matches(raw_matches: list, competition_code: str) -> list:
    """
    Converte a lista bruta da football-data.org para o schema Silver.
    """
    transformed = []
    for m in raw_matches:
        try:
            home = m["homeTeam"]
            away = m["awayTeam"]
            score = m["score"]["fullTime"]
            season = m.get("season", {}).get("startDate", "")[:4]

            transformed.append({
                "id":               m["id"],
                "competition_code": competition_code,
                "season":           season,
                "match_date":       m["utcDate"],
                "status":           m["status"],
                "home_team_id":     home["id"],
                "away_team_id":     away["id"],
                "home_score":       score.get("home"),
                "away_score":       score.get("away"),
                "stage":            m.get("stage", "REGULAR_SEASON"),
            })
        except Exception as e:
            log.warning(f"Erro ao transformar partida {m.get('id')}: {e}")
            continue

    log.info(f"Transformer: {len(transformed)}/{len(raw_matches)} partidas transformadas")
    return transformed

def transform_teams_from_matches(raw_matches: list) -> list:
    """
    Extrai times únicos de uma lista de partidas.
    """
    seen = set()
    teams = []
    for m in raw_matches:
        for side in ["homeTeam", "awayTeam"]:
            t = m[side]
            if t["id"] not in seen:
                seen.add(t["id"])
                teams.append({
                    "id":         t["id"],
                    "name":       t["name"],
                    "short_name": t.get("shortName"),
                    "country":    None,
                })
    return teams

def transform_standings(raw_standings: list, competition_code: str, season: str) -> list:
    """
    Converte a classificação bruta para o schema Silver.
    """
    if not raw_standings:
        return []

    table = raw_standings[0].get("table", [])
    transformed = []
    for row in table:
        try:
            transformed.append({
                "position":      row["position"],
                "team_id":       row["team"]["id"],
                "played":        row["playedGames"],
                "won":           row["won"],
                "draw":          row["draw"],
                "lost":          row["lost"],
                "goals_for":     row["goalsFor"],
                "goals_against": row["goalsAgainst"],
                "goal_diff":     row["goalDifference"],
                "points":        row["points"],
            })
        except Exception as e:
            log.warning(f"Erro ao transformar standing: {e}")
            continue

    return transformed

def transform_teams_from_standings(raw_standings: list) -> list:
    """
    Extrai times únicos da classificação.
    """
    if not raw_standings:
        return []
    seen = set()
    teams = []
    table = raw_standings[0].get("table", [])
    for row in table:
        t = row["team"]
        if t["id"] not in seen:
            seen.add(t["id"])
            teams.append({
                "id":         t["id"],
                "name":       t["name"],
                "short_name": t.get("shortName"),
                "country":    None,
            })
    return teams

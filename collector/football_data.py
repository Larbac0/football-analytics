import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("FOOTBALL_DATA_BASE_URL")
API_KEY  = os.getenv("FOOTBALL_DATA_KEY")

HEADERS = {
    "X-Auth-Token": API_KEY
}

# IDs das ligas no football-data.org
LEAGUES = {
    "premier_league":    "PL",
    "champions_league":  "CL",
    "brasileirao":       "BSA",
    "la_liga":           "PD",
    "bundesliga":        "BL1",
    "serie_a":           "SA",
    "ligue_1":           "FL1",
}

def get_matches(competition: str, date_from: str, date_to: str):
    """
    Busca partidas de uma competição num intervalo de datas.
    competition: código da liga (ex: 'PL')
    date_from / date_to: formato 'YYYY-MM-DD'
    """
    url = f"{BASE_URL}/competitions/{competition}/matches"
    params = {
        "dateFrom": date_from,
        "dateTo":   date_to
    }
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    data = response.json()

    if "errorCode" in data:
        print(f"Erro da API: {data.get('message')}")
        return None

    return data.get("matches", [])


def get_standings(competition: str):
    """
    Busca a classificação atual de uma liga.
    """
    url = f"{BASE_URL}/competitions/{competition}/standings"
    response = requests.get(url, headers=HEADERS, timeout=10)
    data = response.json()

    if "errorCode" in data:
        print(f"Erro da API: {data.get('message')}")
        return None

    return data.get("standings", [])


def get_top_scorers(competition: str):
    """
    Busca os artilheiros de uma liga.
    """
    url = f"{BASE_URL}/competitions/{competition}/scorers"
    response = requests.get(url, headers=HEADERS, timeout=10)
    data = response.json()

    if "errorCode" in data:
        print(f"Erro da API: {data.get('message')}")
        return None

    return data.get("scorers", [])


if __name__ == "__main__":
    from datetime import date, timedelta

    hoje = date.today()
    semana_passada = (hoje - timedelta(days=7)).strftime("%Y-%m-%d")
    hoje_str = hoje.strftime("%Y-%m-%d")

    print("=== PARTIDAS DA SEMANA — PREMIER LEAGUE ===\n")
    matches = get_matches("PL", semana_passada, hoje_str)
    if matches:
        for m in matches:
            home   = m["homeTeam"]["name"]
            away   = m["awayTeam"]["name"]
            status = m["status"]
            data   = m["utcDate"][:10]
            score_h = m["score"]["fullTime"]["home"]
            score_a = m["score"]["fullTime"]["away"]
            placar = f"{score_h} x {score_a}" if score_h is not None else "x"
            print(f"  {data} | {home} {placar} {away} | {status}")
    else:
        print("Nenhuma partida encontrada.")

    print("\n=== CLASSIFICAÇÃO — PREMIER LEAGUE ===\n")
    standings = get_standings("PL")
    if standings:
        tabela = standings[0]["table"]
        for time in tabela[:5]:
            pos  = time["position"]
            nome = time["team"]["name"]
            pts  = time["points"]
            print(f"  {pos}. {nome} — {pts} pts")

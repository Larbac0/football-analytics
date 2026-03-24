import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_FOOTBALL_BASE_URL")
API_KEY  = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

def get_fixtures(date: str, league_id: int, season: int):
    """
    Busca partidas por data, liga e temporada.
    date: formato 'YYYY-MM-DD'
    """
    url = f"{BASE_URL}/fixtures"
    params = {
        "date": date,
        "league": league_id,
        "season": season
    }
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    data = response.json()

    if data.get("errors"):
        print(f"Erro da API: {data['errors']}")
        return None

    print(f"Requisições restantes hoje: {response.headers.get('x-ratelimit-requests-remaining')}")
    return data.get("response", [])


if __name__ == "__main__":
    from datetime import date

    hoje = date.today().strftime("%Y-%m-%d")

    # Premier League, temporada 2024
    fixtures = get_fixtures(date=hoje, league_id=39, season=2024)

    if fixtures:
        print(f"\n{len(fixtures)} partidas encontradas para hoje na Premier League:\n")
        for f in fixtures:
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            hora = f["fixture"]["date"][11:16]
            status = f["fixture"]["status"]["short"]
            print(f"  {hora} | {home} x {away} | status: {status}")
    else:
        print("Nenhuma partida encontrada para hoje.")

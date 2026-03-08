import requests
from datetime import datetime

CITY = {
    "name": "New York",
    "series": "KXHIGHNY"
}

BASE_URL = "https://api.elections.kalshi.com"


def get_kalshi_markets(series):
    try:
        url = f"{BASE_URL}/trade-api/v2/markets"

        r = requests.get(url, timeout=15)
        r.raise_for_status()

        data = r.json()
        markets = data.get("markets", [])

        weather_markets = [
            m for m in markets
            if m.get("ticker", "").startswith(series)
        ]

        return weather_markets

    except Exception as e:
        return [{"title": f"API ERROR: {str(e)}"}]


def scan_weather():

    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    markets = get_kalshi_markets(CITY["series"])

    rows = []

    for m in markets[:20]:

        title = m.get("title", "NO TITLE")

        yes_price = (
            m.get("yes_ask")
            or m.get("yes_bid")
            or "-"
        )

        rows.append({
            "city": CITY["name"],
            "bucket": title,
            "model_prob": "-",
            "kalshi_prob": yes_price,
            "edge": "-",
            "signal": "DEBUG",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": m.get("ticker", "NO TICKER")
        })

    if not rows:
        rows.append({
            "city": CITY["name"],
            "bucket": "No weather markets found",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "NO DATA",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "Kalshi returned no KXHIGHNY markets"
        })

    return rows

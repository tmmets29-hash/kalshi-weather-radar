import requests
from datetime import datetime

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def get_weather_markets():

    try:
        url = f"{BASE_URL}/markets?limit=500"

        r = requests.get(url, timeout=20)
        r.raise_for_status()

        data = r.json()
        markets = data.get("markets", [])

        weather = []

        for m in markets:

            ticker = m.get("ticker","")

            if "TEMP" in ticker:
                weather.append(m)

        return weather

    except Exception as e:

        return [{
            "title": f"API ERROR: {str(e)}",
            "ticker": "NO TICKER"
        }]


def scan_weather():

    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    markets = get_weather_markets()

    rows = []

    for m in markets:

        title = m.get("title","NO TITLE")

        yes_price = (
            m.get("yes_price")
            or m.get("yes_ask")
            or m.get("yes_bid")
            or "-"
        )

        rows.append({
            "city": "Weather",
            "bucket": title,
            "model_prob": "-",
            "kalshi_prob": yes_price,
            "edge": "-",
            "signal": "DEBUG",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": m.get("ticker","NO TICKER")
        })

    if not rows:

        rows.append({
            "city": "Weather",
            "bucket": "No weather markets found",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "NO DATA",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "TEMP ticker filter returned nothing"
        })

    return rows

import requests
from datetime import datetime

CITY = {
    "name": "New York",
    "series": "KXHIGHNY"
}

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def get_kalshi_markets(series):

    markets = []

    try:

        cursor = None

        while True:

            url = f"{BASE_URL}/markets?limit=200"

            if cursor:
                url += f"&cursor={cursor}"

            r = requests.get(url, timeout=15)
            r.raise_for_status()

            data = r.json()

            batch = data.get("markets", [])
            markets.extend(batch)

            cursor = data.get("cursor")

            if not cursor:
                break

            if len(markets) > 2000:
                break

        weather = [
            m for m in markets
            if m.get("ticker", "").startswith(series)
        ]

        return weather

    except Exception as e:
        return [{"title": f"API ERROR: {str(e)}"}]


def scan_weather():

    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    markets = get_kalshi_markets(CITY["series"])

    rows = []

    for m in markets:

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
            "notes": "Series not found in first market pages"
        })

    return rows

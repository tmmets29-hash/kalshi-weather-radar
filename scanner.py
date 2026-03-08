import requests
from datetime import datetime

CITY = {
    "name": "New York",
    "series": "KXHIGHNY"
}

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def get_weather_markets(series):

    try:

        url = f"{BASE_URL}/events"

        r = requests.get(url, timeout=15)
        r.raise_for_status()

        data = r.json()

        events = data.get("events", [])

        weather_events = [
            e for e in events
            if e.get("event_ticker","").startswith(series)
        ]

        markets = []

        for event in weather_events:

            markets.extend(event.get("markets", []))

        return markets

    except Exception as e:

        return [{
            "title": f"API ERROR: {str(e)}",
            "ticker": "NO TICKER"
        }]


def scan_weather():

    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    markets = get_weather_markets(CITY["series"])

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
            "notes": "Series returned no markets"
        })

    return rows

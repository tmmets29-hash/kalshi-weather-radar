import requests
from datetime import datetime

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def scan_weather():
    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rows = []

    try:
        url = f"{BASE_URL}/markets?limit=20"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        markets = data.get("markets", [])

        if not markets:
            return [{
                "city": "-",
                "bucket": "No markets returned",
                "model_prob": "-",
                "kalshi_prob": "-",
                "edge": "-",
                "signal": "NO DATA",
                "suggested_bet": 0,
                "scan_time": scan_time,
                "notes": "Public endpoint returned an empty list",
            }]

        for m in markets[:20]:
            rows.append({
                "city": "-",
                "bucket": m.get("title", "NO TITLE"),
                "model_prob": "-",
                "kalshi_prob": "-",
                "edge": "-",
                "signal": "DEBUG",
                "suggested_bet": 0,
                "scan_time": scan_time,
                "notes": m.get("ticker", "NO TICKER"),
            })

        return rows

    except Exception as e:
        return [{
            "city": "-",
            "bucket": f"API ERROR: {str(e)}",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "ERROR",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "Debug call failed",
        }]

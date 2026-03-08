import requests
from datetime import datetime

CITY = {
    "name": "New York",
    "series": "KXHIGHNY",
    "forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast",
}


def scan_weather():
    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    urls = [
        f"https://api.kalshi.com/trade-api/v2/markets?series_ticker={CITY['series']}",
        f"https://api.kalshi.com/trade-api/v2/markets?series_ticker={CITY['series']}&status=open",
        "https://api.kalshi.com/trade-api/v2/markets?status=open&limit=200",
    ]

    rows = []

    for url in urls:
        try:
            r = requests.get(url, timeout=20)
            status = r.status_code

            try:
                data = r.json()
            except Exception:
                data = {"raw_text": r.text[:500]}

            markets = data.get("markets", []) if isinstance(data, dict) else []

            tickers = []
            for m in markets[:5]:
                tickers.append(m.get("ticker", "NO_TICKER"))

            rows.append({
                "city": CITY["name"],
                "bucket": f"DEBUG {status}",
                "model_prob": len(markets),
                "kalshi_prob": "-",
                "edge": "-",
                "signal": "DEBUG",
                "suggested_bet": 0,
                "scan_time": scan_time,
                "notes": f"url={url} | sample={', '.join(tickers) if tickers else 'none'}",
            })

        except Exception as e:
            rows.append({
                "city": CITY["name"],
                "bucket": "DEBUG ERROR",
                "model_prob": "-",
                "kalshi_prob": "-",
                "edge": "-",
                "signal": "ERROR",
                "suggested_bet": 0,
                "scan_time": scan_time,
                "notes": f"url={url} | error={str(e)}",
            })

    return rows

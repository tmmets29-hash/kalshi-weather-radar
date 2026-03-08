import requests
from datetime import datetime

from weather_model import (
    bucket_probability,
    classify_edge,
    suggested_bet_size,
    adjusted_temperature,
    temperature_std,
)

CITY = {
    "name": "New York",
    "series": "KXHIGHNY",
    "forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast",
}

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def get_forecast(url):
    try:
        headers = {"User-Agent": "kalshi-weather-radar"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        periods = data["properties"]["periods"]

        for p in periods:
            if p.get("isDaytime"):
                temp = p.get("temperature")
                forecast = p.get("shortForecast", "")
                name = p.get("name", "")

                if temp is None:
                    return None, "No temperature"

                return float(temp), f"{name}: {temp}F, {forecast}"

        return None, "No daytime forecast"

    except Exception as e:
        return None, str(e)


def fetch_series_markets(series, status_value):
    url = f"{BASE_URL}/markets?series_ticker={series}&status={status_value}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("markets", [])


def get_kalshi_markets(series):
    try:
        # First try open markets
        markets = fetch_series_markets(series, "open")

        # If nothing is open, fall back to all so we can at least inspect the series
        if not markets:
            markets = fetch_series_markets(series, "all")

        return markets

    except Exception as e:
        return [{"title": f"API ERROR: {str(e)}", "ticker": "NO TICKER"}]


def parse_bucket(title):
    title = title.lower().strip()

    try:
        if "or below" in title:
            num = int(title.split()[0])
            return None, num

        if "or above" in title:
            num = int(title.split()[0])
            return num, None

        if "-" in title:
            parts = title.split("-")
            low = int(parts[0].strip())
            high = int(parts[1].split()[0].strip())
            return low, high

    except Exception:
        pass

    return None, None


def get_market_price(m):
    yes_price = m.get("yes_price")

    if yes_price is None:
        yes_price = m.get("yes_ask")
    if yes_price is None:
        yes_price = m.get("yes_bid")
    if yes_price is None:
        yes_price = m.get("yes_ask_dollars")
    if yes_price is None:
        yes_price = m.get("yes_bid_dollars")

    if yes_price is None:
        return None

    # cents format
    if isinstance(yes_price, (int, float)) and yes_price > 1:
        return float(yes_price) / 100.0

    return float(yes_price)


def scan_weather():
    rows = []
    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    forecast_temp, forecast_note = get_forecast(CITY["forecast"])

    if forecast_temp is None:
        return [{
            "city": CITY["name"],
            "bucket": "Forecast error",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "ERROR",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": forecast_note,
        }]

    markets = get_kalshi_markets(CITY["series"])

    # If the API itself errored, show that directly
    if markets and markets[0].get("title", "").startswith("API ERROR:"):
        return [{
            "city": CITY["name"],
            "bucket": markets[0].get("title"),
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "ERROR",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": markets[0].get("ticker", "NO TICKER"),
        }]

    mean_temp = adjusted_temperature(CITY["name"], forecast_temp)
    std = temperature_std(CITY["name"])

    for m in markets:
        title = m.get("title", "")
        low, high = parse_bucket(title)

        if low is None and high is None:
            continue

        kalshi_prob = get_market_price(m)
        if kalshi_prob is None:
            continue

        try:
            model_prob = bucket_probability(low, high, mean_temp, std)
        except Exception:
            continue

        edge = model_prob - kalshi_prob
        signal = classify_edge(edge, model_prob)
        bet_size = suggested_bet_size(edge)

        rows.append({
            "city": CITY["name"],
            "bucket": title,
            "model_prob": round(model_prob * 100, 1),
            "kalshi_prob": round(kalshi_prob * 100, 1),
            "edge": round(edge * 100, 1),
            "signal": signal,
            "suggested_bet": bet_size,
            "scan_time": scan_time,
            "notes": f"{forecast_note} | {m.get('ticker', 'NO TICKER')}",
        })

    if not rows:
        return [{
            "city": CITY["name"],
            "bucket": "No usable weather buckets found",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "NO DATA",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "Series returned no parseable/priceable bucket markets",
        }]

    rows.sort(key=lambda x: x["edge"], reverse=True)
    return rows

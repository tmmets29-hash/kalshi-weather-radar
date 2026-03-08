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


def get_kalshi_markets(series):
    try:
        # Step 1: get events for the weather series
        url = f"https://api.kalshi.com/trade-api/v2/events?series_ticker={series}"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        events = data.get("events", [])
        if not events:
            return []

        markets = []

        # Step 2: fetch markets for each event
        for e in events:
            event_ticker = e.get("event_ticker")

            m_url = f"https://api.kalshi.com/trade-api/v2/events/{event_ticker}"
            m = requests.get(m_url, timeout=15)
            m.raise_for_status()
            m_data = m.json()

            markets.extend(m_data.get("markets", []))

        return markets

    except Exception:
        return []


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

    mean_temp = adjusted_temperature(CITY["name"], forecast_temp)
    std = temperature_std(CITY["name"])

    for m in markets:
        title = m.get("title", "")

        yes_price = m.get("yes_ask_dollars")
        if yes_price is None:
            yes_price = m.get("yes_bid_dollars")
        if yes_price is None:
            yes_price = m.get("yes_price")

        if yes_price is None:
            continue

        if isinstance(yes_price, (int, float)) and yes_price > 1:
            yes_price = float(yes_price) / 100.0

        low, high = parse_bucket(title)

        try:
            model_prob = bucket_probability(low, high, mean_temp, std)
        except Exception:
            continue

        kalshi_prob = float(yes_price)
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
            "notes": forecast_note,
        })

    if not rows:
        return [{
            "city": CITY["name"],
            "bucket": "No usable markets found",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "NO DATA",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "Kalshi returned no bucket markets",
        }]

    rows.sort(key=lambda x: x["edge"], reverse=True)
    return rows

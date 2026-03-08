import requests
from datetime import datetime

from weather_model import (
    bucket_probability,
    classify_edge,
    suggested_bet_size,
    adjusted_temperature,
    temperature_std,
)

CITIES = [
    {
        "name": "Washington DC",
        "series": "KXHIGHDC",
        "forecast": "https://api.weather.gov/gridpoints/LWX/97,71/forecast",
    }
]


def get_forecast(url):
    try:
        headers = {"User-Agent": "kalshi-weather-radar"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        periods = data["properties"]["periods"]

        for p in periods:
            if p["isDaytime"]:
                temp = p["temperature"]
                forecast = p["shortForecast"]
                name = p["name"]

                if temp is None:
                    return None, "No temperature"

                return float(temp), f"{name}: {temp}F, {forecast}"

        return None, "No daytime forecast"

    except Exception as e:
        return None, str(e)


def get_kalshi_markets(series):
    try:
        url = "https://api.kalshi.com/trade-api/v2/markets?status=open"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        markets = data.get("markets", [])
        return [m for m in markets if m.get("series_ticker") == series]
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

    for city in CITIES:
        forecast_temp, forecast_note = get_forecast(city["forecast"])

        if forecast_temp is None:
            continue

        markets = get_kalshi_markets(city["series"])
        mean_temp = adjusted_temperature(city["name"], forecast_temp)
        std = temperature_std(city["name"])

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

            rows.append(
                {
                    "city": city["name"],
                    "bucket": title,
                    "model_prob": round(model_prob * 100, 1),
                    "kalshi_prob": round(kalshi_prob * 100, 1),
                    "edge": round(edge * 100, 1),
                    "signal": signal,
                    "suggested_bet": bet_size,
                    "scan_time": scan_time,
                    "notes": forecast_note,
                }
            )

    if not rows:
        return [
            {
                "city": "-",
                "bucket": "No usable markets found",
                "model_prob": "-",
                "kalshi_prob": "-",
                "edge": "-",
                "signal": "NO DATA",
                "suggested_bet": 0,
                "scan_time": scan_time,
                "notes": "Weather or Kalshi API returned nothing",
            }
        ]

    best = max(rows, key=lambda x: x["edge"])
    return [best]

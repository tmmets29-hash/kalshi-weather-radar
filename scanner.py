import json
import requests
from datetime import datetime
from weather_model import bucket_probability, classify_edge, suggested_bet_size


CITIES = [

{"name": "Washington DC", "url": "https://api.weather.gov/gridpoints/LWX/97,71/forecast"},
{"name": "New York", "url": "https://api.weather.gov/gridpoints/OKX/33,35/forecast"},
{"name": "Chicago", "url": "https://api.weather.gov/gridpoints/LOT/76,73/forecast"},
{"name": "Dallas", "url": "https://api.weather.gov/gridpoints/FWD/97,58/forecast"},
{"name": "Phoenix", "url": "https://api.weather.gov/gridpoints/PSR/99,76/forecast"}

]


def load_buckets():
    with open("weather_buckets.json", "r") as f:
        return json.load(f)


def get_forecast_mean(url):

    try:

        headers = {"User-Agent": "kalshi-weather-radar"}

        r = requests.get(url, headers=headers, timeout=20)

        r.raise_for_status()

        data = r.json()

        periods = data.get("properties", {}).get("periods", [])

        if not periods:
            return None, None, "No forecast periods returned"

        day_period = None

        for p in periods:
            if p.get("isDaytime"):
                day_period = p
                break

        if day_period is None:
            day_period = periods[0]

        temp = day_period.get("temperature")
        name = day_period.get("name", "Forecast")
        short = day_period.get("shortForecast", "")

        if temp is None:
            return None, None, "No temperature returned"

        std = 4.0

        note = f"{name}: {temp}F, {short}"

        return float(temp), std, note

    except Exception as e:

        return None, None, str(e)


def scan_weather():

    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    rows = []

    buckets = load_buckets()

    for city in CITIES:

        mean, std, forecast_note = get_forecast_mean(city["url"])

        if mean is None:
            continue

        for b in buckets:

            low = b.get("low")
            high = b.get("high")
            kalshi_prob = float(b.get("kalshi_prob", 0))

            model_prob = bucket_probability(low, high, mean, std)

            edge = model_prob - kalshi_prob

            signal = classify_edge(edge, model_prob)

            suggested_bet = suggested_bet_size(edge, bankroll=1000)

            rows.append({

                "city": city["name"],
                "bucket": b.get("label", b.get("bucket", "")),
                "model_prob": round(model_prob * 100, 1),
                "kalshi_prob": round(kalshi_prob * 100, 1),
                "edge": round(edge * 100, 1),
                "signal": signal,
                "suggested_bet": suggested_bet,
                "scan_time": scan_time,
                "notes": forecast_note

            })

    if not rows:

        return [{

            "city": "-",
            "bucket": "No forecast data",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "ERROR",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "Weather API returned nothing"

        }]

    rank = {"OBVIOUS BET": 4, "BET": 3, "WATCH": 2, "PASS": 1}

    rows.sort(key=lambda x: (rank.get(x["signal"], 0), x["edge"]), reverse=True)

    return rows[:10]

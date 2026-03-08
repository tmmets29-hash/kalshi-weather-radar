import json
import requests
from weather_model import bucket_probability, classify_edge


# Washington, DC point forecast from api.weather.gov
GRIDPOINTS_URL = "https://api.weather.gov/gridpoints/LWX/97,71/forecast"


def load_buckets():
    with open("weather_buckets.json", "r") as f:
        return json.load(f)


def get_forecast_mean():
    try:
        headers = {"User-Agent": "kalshi-weather-radar"}
        r = requests.get(GRIDPOINTS_URL, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()

        periods = data.get("properties", {}).get("periods", [])
        if not periods:
            return None, None, "No forecast periods returned"

        # first daytime period is usually today's high forecast
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
            return None, None, "No temperature in forecast"

        # simple starter uncertainty
        std = 2.0

        note = f"{name}: {temp}F, {short}"
        return float(temp), std, note

    except Exception as e:
        return None, None, str(e)


def scan_weather():
    mean, std, forecast_note = get_forecast_mean()

    if mean is None:
        return [{
            "bucket": "Forecast error",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "ERROR",
            "notes": forecast_note
        }]

    buckets = load_buckets()
    rows = []

    for b in buckets:
        low = b.get("low")
        high = b.get("high")
        kalshi_prob = float(b.get("kalshi_prob", 0))

        model_prob = bucket_probability(low, high, mean, std)
        edge = model_prob - kalshi_prob
        signal = classify_edge(edge)

        rows.append({
            "bucket": b.get("label", b.get("bucket", "")),
            "model_prob": round(model_prob * 100, 1),
            "kalshi_prob": round(kalshi_prob * 100, 1),
            "edge": round(edge * 100, 1),
            "signal": signal,
            "notes": forecast_note
        })

    rank = {"OBVIOUS BET": 4, "BET": 3, "WATCH": 2, "PASS": 1}
    rows.sort(key=lambda x: (rank.get(x["signal"], 0), x["edge"]), reverse=True)
    return rows

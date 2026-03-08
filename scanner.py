import json
import requests
from datetime import datetime
from weather_model import bucket_probability, classify_edge, suggested_bet_size


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

        # more realistic starter uncertainty
        std = 4.0

        note = f"{name}: {temp}F, {short}"
        return float(temp), std, note

    except Exception as e:
        return None, None, str(e)


def scan_weather():
    mean, std, forecast_note = get_forecast_mean()
    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if mean is None:
        return [{
            "bucket": "Forecast error",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "ERROR",
            "suggested_bet": 0,
            "scan_time": scan_time,
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
        signal = classify_edge(edge, model_prob)
        suggested_bet = suggested_bet_size(edge, bankroll=1000)

        rows.append({
            "bucket": b.get("label", b.get("bucket", "")),
            "model_prob": round(model_prob * 100, 1),
            "kalshi_prob": round(kalshi_prob * 100, 1),
            "edge": round(edge * 100, 1),
            "signal": signal,
            "suggested_bet": suggested_bet,
            "scan_time": scan_time,
            "notes": forecast_note
        })

    rank = {"OBVIOUS BET": 4, "BET": 3, "WATCH": 2, "PASS": 1}
    rows.sort(key=lambda x: (rank.get(x["signal"], 0), x["edge"]), reverse=True)
    return rows

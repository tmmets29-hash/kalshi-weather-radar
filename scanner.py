import requests
from datetime import datetime

from weather_model import (
    bucket_probability,
    classify_edge,
    suggested_bet_size,
    adjusted_temperature,
    temperature_std
)

# Cities we track
CITIES = [
{
"name": "New York",
"series": "KXHIGHNY",
"forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast"
},
{
"name": "Washington DC",
"series": "KXHIGHDC",
"forecast": "https://api.weather.gov/gridpoints/LWX/97,71/forecast"
},
{
"name": "Chicago",
"series": "KXHIGHCHI",
"forecast": "https://api.weather.gov/gridpoints/LOT/76,73/forecast"
},
{
"name": "Dallas",
"series": "KXHIGHDAL",
"forecast": "https://api.weather.gov/gridpoints/FWD/97,58/forecast"
},
{
"name": "Phoenix",
"series": "KXHIGHPHX",
"forecast": "https://api.weather.gov/gridpoints/PSR/99,76/forecast"
}
]


# Get NOAA forecast temperature
def get_forecast(url):

    try:

        headers = {"User-Agent": "kalshi-weather-radar"}

        r = requests.get(url, headers=headers, timeout=20)

        r.raise_for_status()

        data = r.json()

        periods = data["properties"]["periods"]

        for p in periods:

            if p["isDaytime"]:

                temp = p["temperature"]

                short = p["shortForecast"]

                name = p["name"]

                return float(temp), f"{name}: {temp}F, {short}"

        return None, "No daytime forecast"

    except Exception as e:

        return None, str(e)


# Get Kalshi markets
def get_kalshi_markets(series):

    try:

        url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open"

        r = requests.get(url, timeout=20)

        r.raise_for_status()

        data = r.json()

        return data.get("markets", [])

    except:

        return []


# Convert bucket title to numeric range
def parse_bucket(title):

    title = title.lower()

    try:

        if "or below" in title:

            num = int(title.split()[0])

            return None, num

        if "or above" in title:

            num = int(title.split()[0])

            return num, None

        if "-" in title:

            parts = title.split("-")

            low = int(parts[0])

            high = int(parts[1].split()[0])

            return low, high

    except:

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

        # Apply bias correction
        mean_temp = adjusted_temperature(city["name"], forecast_temp)

        # City volatility
        std = temperature_std(city["name"])

        for m in markets:

            title = m.get("title", "")

            yes_price = m.get("yes_ask_dollars")

            if yes_price is None:
                yes_price = m.get("yes_bid_dollars")

            if yes_price is None:
                continue

            low, high = parse_bucket(title)

            model_prob = bucket_probability(low, high, mean_temp, std)

            kalshi_prob = float(yes_price)

            edge = model_prob - kalshi_prob

            signal = classify_edge(edge, model_prob)

            bet_size = suggested_bet_size(edge)

            rows.append({

                "city": city["name"],
                "bucket": title,
                "model_prob": round(model_prob * 100, 1),
                "kalshi_prob": round(kalshi_prob * 100, 1),
                "edge": round(edge * 100, 1),
                "signal": signal,
                "suggested_bet": bet_size,
                "scan_time": scan_time,
                "notes": forecast_note

            })

    if not rows:

        return [{
            "city": "-",
            "bucket": "No markets found",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "ERROR",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "Kalshi or weather API returned nothing"
        }]

    # Pick best bet per city
    best_by_city = {}

    for r in rows:

        city = r["city"]

        if city not in best_by_city:

            best_by_city[city] = r

            continue

        if r["edge"] > best_by_city[city]["edge"]:

            best_by_city[city] = r

    return list(best_by_city.values())

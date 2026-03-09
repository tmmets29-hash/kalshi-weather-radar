import os
import time
import base64
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE_URL = "https://trading-api.kalshi.com"
PATH = "/trade-api/v2/markets?series_ticker=KXHIGHNY"

API_KEY = os.getenv("KALSHI_API_KEY")

with open("/etc/secrets/kalshi_private_key.pem", "rb") as f:
    PRIVATE_KEY = serialization.load_pem_private_key(f.read(), password=None)

def sign_request(timestamp, method, path):
    message = f"{timestamp}{method}{path}".encode()

    signature = PRIVATE_KEY.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode()

def get_weather_markets():

    timestamp = str(int(time.time() * 1000))
    method = "GET"

    signature = sign_request(timestamp, method, PATH)

    headers = {
        "KALSHI-ACCESS-KEY": API_KEY,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
    }

    url = BASE_URL + PATH

    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()

    data = r.json()

    return data.get("markets", [])

def scan_weather():

    markets = get_weather_markets()
    results = []

    for m in markets:
        results.append({
            "city": "New York",
            "bucket": m.get("title"),
            "kalshi_prob": m.get("yes_price", "-"),
            "model_prob": "-",
            "edge": "-",
            "signal": "DEBUG",
            "suggested_bet": 0,
            "notes": m.get("ticker"),
        })

    if not results:
        results.append({
            "city": "New York",
            "bucket": "No weather markets found",
            "kalshi_prob": "-",
            "model_prob": "-",
            "edge": "-",
            "signal": "NO DATA",
            "suggested_bet": 0,
            "notes": "No markets returned",
        })

    return results

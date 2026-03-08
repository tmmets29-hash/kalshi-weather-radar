import os
import time
import base64
import requests

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

CITY = {
    "name": "New York",
    "series": "KXHIGHNY",
}

BASE_URL = "https://trading-api.kalshi.com"
PATH = f"/trade-api/v2/markets?series_ticker={CITY['series']}"

KALSHI_API_KEY = os.getenv("KALSHI_API_KEY")

with open("/etc/secrets/kalshi_private_key.pem", "r") as f:
    KALSHI_API_SECRET = f.read()


def sign_pss_text(private_key_pem: str, message: str) -> str:
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
    )

    signature = private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode()


def kalshi_headers(method: str, path: str) -> dict:
    timestamp = str(int(time.time() * 1000))
    message = timestamp + method.upper() + path
    signature_b64 = sign_pss_text(KALSHI_API_SECRET, message)

    return {
        "KALSHI-ACCESS-KEY": KALSHI_API_KEY,
        "KALSHI-ACCESS-SIGNATURE": signature_b64,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def get_weather_markets():
    if not KALSHI_API_KEY:
        return [{
            "title": "Missing KALSHI_API_KEY",
            "ticker": "NO TICKER",
        }]

    try:
        headers = kalshi_headers("GET", PATH)
        url = BASE_URL + PATH

        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()

        data = r.json()
        return data.get("markets", [])

    except Exception as e:
        return [{
            "title": f"API ERROR: {str(e)}",
            "ticker": "NO TICKER",
        }]


def scan_weather():
    scan_time = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    markets = get_weather_markets()

    rows = []

    for m in markets:
        title = m.get("title", "NO TITLE")

        yes_price = (
            m.get("yes_price")
            or m.get("yes_ask")
            or m.get("yes_bid")
            or m.get("yes_ask_dollars")
            or m.get("yes_bid_dollars")
            or "-"
        )

        rows.append({
            "city": CITY["name"],
            "bucket": title,
            "model_prob": "-",
            "kalshi_prob": yes_price,
            "edge": "-",
            "signal": "DEBUG",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": m.get("ticker", "NO TICKER"),
        })

    if not rows:
        rows.append({
            "city": CITY["name"],
            "bucket": "No weather markets found",
            "model_prob": "-",
            "kalshi_prob": "-",
            "edge": "-",
            "signal": "NO DATA",
            "suggested_bet": 0,
            "scan_time": scan_time,
            "notes": "Authenticated API returned no markets",
        })

    return rows

import os
import time
import base64
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE_URL = "https://api.elections.kalshi.com"
REQUEST_PATH = "/trade-api/v2/markets"
QUERY = "series_ticker=KXHIGHNY&status=all&limit=1000"

API_KEY = os.getenv("KALSHI_API_KEY")


def format_row(city, bucket, model_prob="-", kalshi_prob="-", edge="-",
               signal="DEBUG", suggested_bet=0, notes=""):
    return {
        "city": city,
        "bucket": bucket,
        "model_prob": model_prob,
        "kalshi_prob": kalshi_prob,
        "edge": edge,
        "signal": signal,
        "suggested_bet": suggested_bet,
        "notes": notes,
    }


def load_private_key():
    with open("/etc/secrets/kalshi_private_key.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def sign_request(private_key, timestamp, method, path_without_query):
    message = f"{timestamp}{method}{path_without_query}".encode()

    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode()


def get_weather_markets():
    try:
        if not API_KEY:
            return [format_row(
                city="Scanner Error",
                bucket="Missing KALSHI_API_KEY",
                signal="ERROR",
                notes="env var missing"
            )]

        private_key = load_private_key()

        timestamp = str(int(time.time() * 1000))
        signature = sign_request(private_key, timestamp, "GET", REQUEST_PATH)

        headers = {
            "KALSHI-ACCESS-KEY": API_KEY,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{BASE_URL}{REQUEST_PATH}?{QUERY}"
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()

        data = r.json()
        markets = data.get("markets", [])

        rows = []
        for m in markets:
            rows.append(format_row(
                city="New York",
                bucket=m.get("title", "NO TITLE"),
                kalshi_prob=(
                    m.get("yes_price")
                    or m.get("yes_ask")
                    or m.get("yes_bid")
                    or m.get("yes_ask_dollars")
                    or m.get("yes_bid_dollars")
                    or "-"
                ),
                notes=m.get("ticker", "NO TICKER")
            ))

        if not rows:
            rows.append(format_row(
                city="New York",
                bucket="No weather markets found",
                signal="NO DATA",
                notes="empty result"
            ))

        return rows

    except Exception as e:
        return [format_row(
            city="Scanner Error",
            bucket=str(e),
            signal="ERROR",
            notes="scanner exception"
        )]


def scan_weather():
    return get_weather_markets()

import os
import time
import base64
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE_URL = "https://trading-api.kalshi.com"
PATH = "/trade-api/v2/markets?series_ticker=KXHIGHNY"

API_KEY = os.getenv("KALSHI_API_KEY")


def load_private_key():
    with open("/etc/secrets/kalshi_private_key.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def sign_request(private_key, timestamp, method, path):
    message = f"{timestamp}{method}{path}".encode()

    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode()


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
        method = "GET"

        signature = sign_request(private_key, timestamp, method, PATH)

        headers = {
            "KALSHI-ACCESS-KEY": API_KEY,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
        }

        r = requests.get(BASE_URL + PATH, headers=headers, timeout=20)
        r.raise_for_status()

        data = r.json()
        markets = data.get("markets", [])

        results = []

        for m in markets:
            results.append(format_row(
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
                signal="DEBUG",
                notes=m.get("ticker", "NO TICKER")
            ))

        if not results:
            results.append(format_row(
                city="New York",
                bucket="No weather markets found",
                signal="NO DATA",
                notes="empty result"
            ))

        return results

    except Exception as e:
        return [format_row(
            city="Scanner Error",
            bucket=str(e),
            signal="ERROR",
            notes="scanner exception"
        )]


def scan_weather():
    return get_weather_markets()

import math

# Normal distribution helper
def normal_cdf(x, mean, std):
    z = (x - mean) / std
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# Historical forecast bias by city
CITY_BIAS = {
    "New York": -0.8,
    "Washington DC": -0.5,
    "Chicago": -1.2,
    "Dallas": -0.3,
    "Phoenix": 0.4
}


# Forecast volatility by city
CITY_STD = {
    "New York": 4,
    "Washington DC": 4,
    "Chicago": 5,
    "Dallas": 4.5,
    "Phoenix": 2.5
}


def adjusted_temperature(city, forecast_temp):
    bias = CITY_BIAS.get(city, 0)
    return forecast_temp + bias


def temperature_std(city):
    return CITY_STD.get(city, 4)


def bucket_probability(low, high, mean, std):

    if low is None:
        return normal_cdf(high, mean, std)

    if high is None:
        return 1 - normal_cdf(low, mean, std)

    return normal_cdf(high, mean, std) - normal_cdf(low, mean, std)


def classify_edge(edge, model_prob):

    if edge > 0.15 and model_prob > 0.15:
        return "OBVIOUS BET"

    if edge > 0.08:
        return "BET"

    if edge > 0.03:
        return "WATCH"

    return "PASS"


def suggested_bet_size(edge):

    if edge > 0.20:
        return 150

    if edge > 0.15:
        return 100

    if edge > 0.10:
        return 60

    if edge > 0.05:
        return 30

    return 0

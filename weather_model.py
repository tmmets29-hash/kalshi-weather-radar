import math


def normal_cdf(x, mean, std):

    if std <= 0:
        return 1.0 if x >= mean else 0.0

    z = (x - mean) / (std * math.sqrt(2))

    return 0.5 * (1 + math.erf(z))


def bucket_probability(low, high, mean, std):

    if low is None and high is None:
        return 0.0

    if low is None:
        return normal_cdf(high + 0.5, mean, std)

    if high is None:
        return 1 - normal_cdf(low - 0.5, mean, std)

    upper = normal_cdf(high + 0.5, mean, std)
    lower = normal_cdf(low - 0.5, mean, std)

    return max(0.0, upper - lower)


def expected_value(model_prob, market_prob):

    payout = (1 / market_prob) - 1

    win = model_prob * payout
    loss = (1 - model_prob)

    ev = win - loss

    return ev


def kelly_fraction(model_prob, market_prob):

    b = (1 / market_prob) - 1
    p = model_prob
    q = 1 - p

    numerator = (b * p) - q

    if numerator <= 0:
        return 0

    kelly = numerator / b

    return max(0, kelly)


def suggested_bet_size(edge, bankroll=1000):

    # fallback rule if EV not used
    if edge >= 0.10:
        return round(bankroll * 0.025, 2)

    if edge >= 0.05:
        return round(bankroll * 0.01, 2)

    if edge >= 0.03:
        return round(bankroll * 0.005, 2)

    return 0


def suggested_kelly_bet(model_prob, market_prob, bankroll=1000):

    kelly = kelly_fraction(model_prob, market_prob)

    # use quarter Kelly for safety
    kelly = kelly * 0.25

    return round(bankroll * kelly, 2)


def classify_edge(edge, model_prob):

    if edge >= 0.12 and 0.10 < model_prob < 0.90:
        return "OBVIOUS BET"

    if edge >= 0.06:
        return "BET"

    if edge >= 0.03:
        return "WATCH"

    return "PASS"

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


def classify_edge(edge):
    if edge >= 0.08:
        return "OBVIOUS BET"
    if edge >= 0.05:
        return "BET"
    if edge >= 0.03:
        return "WATCH"
    return "PASS"

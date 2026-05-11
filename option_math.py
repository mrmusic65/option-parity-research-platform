import math
from dataclasses import dataclass


@dataclass
class BlackScholesResult:
    option_type: str
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    dividend_yield: float
    volatility: float
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    d1: float
    d2: float


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def calculate_d1(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
) -> float:
    numerator = math.log(spot / strike) + (
        risk_free_rate - dividend_yield + 0.5 * volatility * volatility
    ) * time_to_expiry

    denominator = volatility * math.sqrt(time_to_expiry)

    return numerator / denominator


def calculate_d2(d1: float, volatility: float, time_to_expiry: float) -> float:
    return d1 - volatility * math.sqrt(time_to_expiry)


def black_scholes_price_and_greeks(
    option_type: str,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
) -> BlackScholesResult:
    option_type = option_type.lower().strip()

    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be either 'call' or 'put'.")

    if spot <= 0:
        raise ValueError("spot must be greater than zero.")

    if strike <= 0:
        raise ValueError("strike must be greater than zero.")

    if time_to_expiry <= 0:
        raise ValueError("time_to_expiry must be greater than zero.")

    if volatility <= 0:
        raise ValueError("volatility must be greater than zero.")

    d1 = calculate_d1(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
    )

    d2 = calculate_d2(
        d1=d1,
        volatility=volatility,
        time_to_expiry=time_to_expiry,
    )

    discount_stock = math.exp(-dividend_yield * time_to_expiry)
    discount_strike = math.exp(-risk_free_rate * time_to_expiry)

    if option_type == "call":
        price = (
            spot * discount_stock * normal_cdf(d1)
            - strike * discount_strike * normal_cdf(d2)
        )

        delta = discount_stock * normal_cdf(d1)

        theta = (
            -spot
            * discount_stock
            * normal_pdf(d1)
            * volatility
            / (2.0 * math.sqrt(time_to_expiry))
            - risk_free_rate * strike * discount_strike * normal_cdf(d2)
            + dividend_yield * spot * discount_stock * normal_cdf(d1)
        )

        rho = strike * time_to_expiry * discount_strike * normal_cdf(d2)

    else:
        price = (
            strike * discount_strike * normal_cdf(-d2)
            - spot * discount_stock * normal_cdf(-d1)
        )

        delta = discount_stock * (normal_cdf(d1) - 1.0)

        theta = (
            -spot
            * discount_stock
            * normal_pdf(d1)
            * volatility
            / (2.0 * math.sqrt(time_to_expiry))
            + risk_free_rate * strike * discount_strike * normal_cdf(-d2)
            - dividend_yield * spot * discount_stock * normal_cdf(-d1)
        )

        rho = -strike * time_to_expiry * discount_strike * normal_cdf(-d2)

    gamma = (
        discount_stock
        * normal_pdf(d1)
        / (spot * volatility * math.sqrt(time_to_expiry))
    )

    vega = spot * discount_stock * normal_pdf(d1) * math.sqrt(time_to_expiry)

    return BlackScholesResult(
        option_type=option_type,
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        price=round(price, 6),
        delta=round(delta, 6),
        gamma=round(gamma, 6),
        vega=round(vega / 100.0, 6),
        theta=round(theta / 365.0, 6),
        rho=round(rho / 100.0, 6),
        d1=round(d1, 6),
        d2=round(d2, 6),
    )
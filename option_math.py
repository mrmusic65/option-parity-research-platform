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


@dataclass
class ImpliedVolatilityResult:
    option_type: str
    market_price: float
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    dividend_yield: float
    implied_volatility: float | None
    model_price: float | None
    pricing_error: float | None
    converged: bool
    iterations: int
    message: str


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


def intrinsic_value(
    option_type: str,
    spot: float,
    strike: float,
    dividend_yield: float,
    time_to_expiry: float,
) -> float:
    option_type = option_type.lower().strip()
    dividend_adjusted_spot = spot * math.exp(-dividend_yield * time_to_expiry)

    if option_type == "call":
        return max(0.0, dividend_adjusted_spot - strike)

    if option_type == "put":
        return max(0.0, strike - dividend_adjusted_spot)

    raise ValueError("option_type must be either 'call' or 'put'.")


def implied_volatility_bisection(
    option_type: str,
    market_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    dividend_yield: float,
    min_vol: float = 0.0001,
    max_vol: float = 5.0,
    tolerance: float = 1e-6,
    max_iterations: int = 100,
) -> ImpliedVolatilityResult:
    option_type = option_type.lower().strip()

    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be either 'call' or 'put'.")

    if market_price <= 0:
        return ImpliedVolatilityResult(
            option_type=option_type,
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            implied_volatility=None,
            model_price=None,
            pricing_error=None,
            converged=False,
            iterations=0,
            message="Market price must be greater than zero.",
        )

    if spot <= 0 or strike <= 0 or time_to_expiry <= 0:
        return ImpliedVolatilityResult(
            option_type=option_type,
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            implied_volatility=None,
            model_price=None,
            pricing_error=None,
            converged=False,
            iterations=0,
            message="Invalid spot, strike, or time to expiry.",
        )

    lower_bound_price = intrinsic_value(
        option_type=option_type,
        spot=spot,
        strike=strike,
        dividend_yield=dividend_yield,
        time_to_expiry=time_to_expiry,
    )

    if market_price < lower_bound_price:
        return ImpliedVolatilityResult(
            option_type=option_type,
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            implied_volatility=None,
            model_price=None,
            pricing_error=None,
            converged=False,
            iterations=0,
            message="Market price is below intrinsic value; implied volatility is invalid.",
        )

    low = min_vol
    high = max_vol

    low_price = black_scholes_price_and_greeks(
        option_type=option_type,
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=low,
    ).price

    high_price = black_scholes_price_and_greeks(
        option_type=option_type,
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=high,
    ).price

    if market_price < low_price or market_price > high_price:
        return ImpliedVolatilityResult(
            option_type=option_type,
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            implied_volatility=None,
            model_price=None,
            pricing_error=None,
            converged=False,
            iterations=0,
            message="Market price is outside model price bounds.",
        )

    mid = None
    model_price = None
    pricing_error = None

    for iteration in range(1, max_iterations + 1):
        mid = (low + high) / 2.0

        result = black_scholes_price_and_greeks(
            option_type=option_type,
            spot=spot,
            strike=strike,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            volatility=mid,
        )

        model_price = result.price
        pricing_error = model_price - market_price

        if abs(pricing_error) < tolerance:
            return ImpliedVolatilityResult(
                option_type=option_type,
                market_price=market_price,
                spot=spot,
                strike=strike,
                time_to_expiry=time_to_expiry,
                risk_free_rate=risk_free_rate,
                dividend_yield=dividend_yield,
                implied_volatility=round(mid, 6),
                model_price=round(model_price, 6),
                pricing_error=round(pricing_error, 8),
                converged=True,
                iterations=iteration,
                message="Converged.",
            )

        if model_price > market_price:
            high = mid
        else:
            low = mid

    return ImpliedVolatilityResult(
        option_type=option_type,
        market_price=market_price,
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        implied_volatility=round(mid, 6) if mid is not None else None,
        model_price=round(model_price, 6) if model_price is not None else None,
        pricing_error=round(pricing_error, 8) if pricing_error is not None else None,
        converged=False,
        iterations=max_iterations,
        message="Maximum iterations reached.",
    )
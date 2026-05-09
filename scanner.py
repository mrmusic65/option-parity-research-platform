import yfinance as yf
import pandas as pd
from math import exp, log, isfinite
from datetime import datetime


def year_fraction(expiry: str) -> float:
    expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
    today = datetime.today()
    return max((expiry_date - today).days / 365, 0)


def get_option_chain(ticker: str, expiry: str):
    stock = yf.Ticker(ticker)
    chain = stock.option_chain(expiry)

    hist = stock.history(period="5d")
    if hist.empty:
        raise ValueError("Could not fetch stock price.")

    spot = hist["Close"].iloc[-1]
    return spot, chain.calls, chain.puts


def safe_implied_rate(spot, dividend_yield, strike, parity, T):
    try:
        if T <= 0:
            return None

        numerator = spot * exp(-dividend_yield * T) - parity

        if numerator <= 0 or strike <= 0:
            return None

        implied_rate = -log(numerator / strike) / T

        if not isfinite(implied_rate):
            return None

        return implied_rate

    except Exception:
        return None


def safe_implied_dividend_yield(spot, risk_free_rate, strike, parity, T):
    try:
        if T <= 0:
            return None

        pv_k = strike * exp(-risk_free_rate * T)
        numerator = parity + pv_k

        if numerator <= 0 or spot <= 0:
            return None

        implied_q = -log(numerator / spot) / T

        if not isfinite(implied_q):
            return None

        return implied_q

    except Exception:
        return None


def liquidity_score(
    call_bid,
    call_ask,
    put_bid,
    put_ask,
    call_volume,
    put_volume,
    call_oi,
    put_oi
):
    call_spread = max(call_ask - call_bid, 0)
    put_spread = max(put_ask - put_bid, 0)
    total_spread = call_spread + put_spread

    volume_score = min((call_volume + put_volume) / 2000, 1) * 35
    oi_score = min((call_oi + put_oi) / 10000, 1) * 35
    spread_score = max(0, 1 - total_spread / 2) * 30

    return round(volume_score + oi_score + spread_score, 2)


def classify_data_quality(
    spot,
    strike,
    call_bid,
    call_ask,
    put_bid,
    put_ask,
    call_volume,
    put_volume,
    call_oi,
    put_oi,
    total_spread,
    min_total_spread_floor,
    max_moneyness_deviation,
    min_option_bid,
):
    issues = []

    if spot <= 0 or strike <= 0:
        issues.append("invalid spot or strike")

    moneyness_deviation = abs(strike / spot - 1)

    if moneyness_deviation > max_moneyness_deviation:
        issues.append("strike too far from spot")

    if call_ask <= 0 or put_ask <= 0:
        issues.append("invalid ask price")

    if call_bid < 0 or put_bid < 0:
        issues.append("invalid bid price")

    if call_ask < call_bid or put_ask < put_bid:
        issues.append("crossed option quote")

    if call_bid < min_option_bid and put_bid < min_option_bid:
        issues.append("both option bids near zero")

    if total_spread < min_total_spread_floor:
        issues.append("spread floor triggered")

    if (call_volume + put_volume) == 0 and (call_oi + put_oi) < 100:
        issues.append("stale or inactive quote")

    if not issues:
        return "OK"

    return "; ".join(issues)


def classify_market_diagnostic(
    implied_rate_mid,
    implied_dividend_yield_mid,
    risk_free_rate,
    dividend_yield,
    edge_to_spread,
    total_spread,
    T,
    data_quality,
):
    diagnostics = []

    if data_quality != "OK":
        diagnostics.append("data quality issue")

    if implied_rate_mid is not None:
        rate_gap = implied_rate_mid - risk_free_rate

        if abs(rate_gap) > 0.10:
            diagnostics.append("large implied financing deviation")

        if implied_rate_mid < -0.05:
            diagnostics.append("negative implied financing rate")

    if implied_dividend_yield_mid is not None:
        q_gap = implied_dividend_yield_mid - dividend_yield

        if abs(q_gap) > 0.05:
            diagnostics.append("large implied dividend deviation")

        if implied_dividend_yield_mid < -0.02:
            diagnostics.append("negative implied dividend yield")

    if edge_to_spread < 0.5:
        diagnostics.append("weak edge relative to spread")

    if total_spread > 1.00:
        diagnostics.append("wide option market")

    if T < 7 / 365:
        diagnostics.append("very short maturity")

    if not diagnostics:
        return "normal relative-value candidate"

    return "; ".join(diagnostics)


def classify_risk_note(
    T,
    total_spread,
    total_oi,
    dividend_yield,
    executable_edge_after_costs,
    liquidity_score_value,
    edge_to_spread,
    data_quality,
):
    notes = []

    if data_quality != "OK":
        notes.append(f"Data quality flag: {data_quality}")

    if T < 7 / 365:
        notes.append("Very short expiry; execution and pin risk elevated")

    if total_spread > 1.00:
        notes.append("Wide option spread")

    if total_oi < 500:
        notes.append("Low open interest")

    if dividend_yield > 0:
        notes.append("Dividend adjustment estimated, not exact cash dividends")

    if executable_edge_after_costs <= 0:
        notes.append("No executable edge after conservative costs")

    if liquidity_score_value < 50:
        notes.append("Weak liquidity score")

    if edge_to_spread < 1:
        notes.append("Edge is small relative to total spread")

    if not notes:
        return "Clean research candidate under current filters"

    return "; ".join(notes)


def scan_put_call_parity(
    ticker: str,
    expiry: str,
    risk_free_rate=0.05,
    dividend_yield=0.00,
    stock_slippage_bps=2.0,
    min_net_edge=0.05,
    max_total_spread=1.00,
    min_open_interest=500,
    min_liquidity_score=50,
    min_edge_to_spread=0.50,
    min_total_spread_floor=0.05,
    max_moneyness_deviation=0.20,
    min_option_bid=0.01,
):
    spot, calls, puts = get_option_chain(ticker, expiry)
    T = year_fraction(expiry)

    calls = calls[[
        "strike",
        "bid",
        "ask",
        "lastPrice",
        "volume",
        "openInterest"
    ]]

    puts = puts[[
        "strike",
        "bid",
        "ask",
        "lastPrice",
        "volume",
        "openInterest"
    ]]

    df = pd.merge(
        calls,
        puts,
        on="strike",
        suffixes=("_call", "_put")
    )

    results = []

    stock_slippage_cost = spot * (stock_slippage_bps / 10000)

    for _, row in df.iterrows():
        K = row["strike"]

        call_bid = row["bid_call"]
        call_ask = row["ask_call"]
        put_bid = row["bid_put"]
        put_ask = row["ask_put"]

        call_volume = row["volume_call"] if pd.notna(row["volume_call"]) else 0
        put_volume = row["volume_put"] if pd.notna(row["volume_put"]) else 0
        call_oi = row["openInterest_call"] if pd.notna(row["openInterest_call"]) else 0
        put_oi = row["openInterest_put"] if pd.notna(row["openInterest_put"]) else 0

        if call_ask < call_bid or put_ask < put_bid:
            continue

        if call_ask <= 0 or put_ask <= 0:
            continue

        call_spread = call_ask - call_bid
        put_spread = put_ask - put_bid
        total_spread = call_spread + put_spread

        data_quality = classify_data_quality(
            spot=spot,
            strike=K,
            call_bid=call_bid,
            call_ask=call_ask,
            put_bid=put_bid,
            put_ask=put_ask,
            call_volume=call_volume,
            put_volume=put_volume,
            call_oi=call_oi,
            put_oi=put_oi,
            total_spread=total_spread,
            min_total_spread_floor=min_total_spread_floor,
            max_moneyness_deviation=max_moneyness_deviation,
            min_option_bid=min_option_bid,
        )

        moneyness = K / spot

        pv_k = K * exp(-risk_free_rate * T)

        dividend_adjusted_spot = spot * exp(-dividend_yield * T)
        theoretical_parity = dividend_adjusted_spot - pv_k

        call_mid = (call_bid + call_ask) / 2
        put_mid = (put_bid + put_ask) / 2
        mid_market_parity = call_mid - put_mid
        mid_mispricing = mid_market_parity - theoretical_parity

        implied_rate_mid = safe_implied_rate(
            spot=spot,
            dividend_yield=dividend_yield,
            strike=K,
            parity=mid_market_parity,
            T=T
        )

        implied_dividend_yield_mid = safe_implied_dividend_yield(
            spot=spot,
            risk_free_rate=risk_free_rate,
            strike=K,
            parity=mid_market_parity,
            T=T
        )

        long_synth_cost = call_ask - put_bid
        long_synth_edge_before_stock_cost = theoretical_parity - long_synth_cost
        long_synth_edge_after_costs = (
            long_synth_edge_before_stock_cost
            - stock_slippage_cost
        )

        short_synth_credit = call_bid - put_ask
        short_synth_edge_before_stock_cost = short_synth_credit - theoretical_parity
        short_synth_edge_after_costs = (
            short_synth_edge_before_stock_cost
            - stock_slippage_cost
        )

        if long_synth_edge_after_costs > short_synth_edge_after_costs:
            best_trade = "Buy synthetic forward"
            executable_edge_before_costs = long_synth_edge_before_stock_cost
            executable_edge_after_costs = long_synth_edge_after_costs
        else:
            best_trade = "Sell synthetic forward"
            executable_edge_before_costs = short_synth_edge_before_stock_cost
            executable_edge_after_costs = short_synth_edge_after_costs

        total_oi = call_oi + put_oi

        liq_score = liquidity_score(
            call_bid,
            call_ask,
            put_bid,
            put_ask,
            call_volume,
            put_volume,
            call_oi,
            put_oi
        )

        effective_spread_for_ratio = max(total_spread, min_total_spread_floor)

        edge_to_spread = (
            executable_edge_after_costs / effective_spread_for_ratio
            if effective_spread_for_ratio > 0
            else 0
        )

        passes_filters = (
            data_quality == "OK"
            and executable_edge_after_costs > min_net_edge
            and total_spread <= max_total_spread
            and total_oi >= min_open_interest
            and liq_score >= min_liquidity_score
            and edge_to_spread >= min_edge_to_spread
        )

        if passes_filters:
            signal = "Research candidate"
        elif executable_edge_after_costs > 0 and data_quality == "OK":
            signal = "Watchlist"
        elif data_quality != "OK":
            signal = "Data quality issue"
        else:
            signal = "No trade"

        confidence_score = 0

        if executable_edge_after_costs > 0:
            confidence_score += min(executable_edge_after_costs / 1.0, 1) * 25

        confidence_score += min(liq_score / 100, 1) * 25

        if total_spread <= max_total_spread:
            confidence_score += 15

        if total_oi >= min_open_interest:
            confidence_score += 15

        if edge_to_spread >= min_edge_to_spread:
            confidence_score += 10

        if data_quality == "OK":
            confidence_score += 10

        confidence_score = round(confidence_score, 2)

        market_diagnostic = classify_market_diagnostic(
            implied_rate_mid=implied_rate_mid,
            implied_dividend_yield_mid=implied_dividend_yield_mid,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            edge_to_spread=edge_to_spread,
            total_spread=total_spread,
            T=T,
            data_quality=data_quality,
        )

        risk_note = classify_risk_note(
            T=T,
            total_spread=total_spread,
            total_oi=total_oi,
            dividend_yield=dividend_yield,
            executable_edge_after_costs=executable_edge_after_costs,
            liquidity_score_value=liq_score,
            edge_to_spread=edge_to_spread,
            data_quality=data_quality,
        )

        results.append({
            "ticker": ticker,
            "expiry": expiry,
            "spot": round(spot, 2),
            "strike": K,
            "moneyness": round(moneyness, 4),

            "call_bid": call_bid,
            "call_ask": call_ask,
            "put_bid": put_bid,
            "put_ask": put_ask,

            "risk_free_rate": risk_free_rate,
            "dividend_yield": dividend_yield,
            "T_years": round(T, 6),

            "pv_strike": round(pv_k, 4),
            "dividend_adjusted_spot": round(dividend_adjusted_spot, 4),
            "theoretical_parity": round(theoretical_parity, 4),

            "mid_market_parity": round(mid_market_parity, 4),
            "mid_mispricing": round(mid_mispricing, 4),

            "implied_rate_mid": round(implied_rate_mid, 6) if implied_rate_mid is not None else None,
            "implied_dividend_yield_mid": round(implied_dividend_yield_mid, 6) if implied_dividend_yield_mid is not None else None,

            "long_synth_cost": round(long_synth_cost, 4),
            "long_synth_edge_after_costs": round(long_synth_edge_after_costs, 4),

            "short_synth_credit": round(short_synth_credit, 4),
            "short_synth_edge_after_costs": round(short_synth_edge_after_costs, 4),

            "best_trade": best_trade,
            "executable_edge_before_costs": round(executable_edge_before_costs, 4),
            "stock_slippage_cost": round(stock_slippage_cost, 4),
            "executable_edge_after_costs": round(executable_edge_after_costs, 4),

            "edge_to_spread": round(edge_to_spread, 4),

            "call_spread": round(call_spread, 4),
            "put_spread": round(put_spread, 4),
            "total_spread": round(total_spread, 4),
            "effective_spread_for_ratio": round(effective_spread_for_ratio, 4),

            "call_volume": call_volume,
            "put_volume": put_volume,
            "call_oi": call_oi,
            "put_oi": put_oi,
            "total_oi": total_oi,

            "liquidity_score": liq_score,
            "confidence_score": confidence_score,
            "signal": signal,
            "data_quality": data_quality,
            "market_diagnostic": market_diagnostic,
            "risk_note": risk_note,
        })

    if not results:
        return pd.DataFrame()

    signal_rank = {
        "Research candidate": 0,
        "Watchlist": 1,
        "Data quality issue": 2,
        "No trade": 3,
    }

    output = pd.DataFrame(results)
    output["signal_rank"] = output["signal"].map(signal_rank)

    output = output.sort_values(
        ["signal_rank", "confidence_score", "executable_edge_after_costs"],
        ascending=[True, False, False]
    )

    return output.drop(columns=["signal_rank"])
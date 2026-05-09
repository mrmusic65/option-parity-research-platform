from pathlib import Path
import sys
from typing import Any

import pandas as pd
import yfinance as yf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from scanner import scan_put_call_parity
from research import (
    load_all_snapshots,
    summarize_research_history,
    signal_decay_analysis,
    signal_persistence_score,
    save_scan_snapshot,
)


app = FastAPI(
    title="Options Relative Value API",
    version="0.1.0",
    description="Backend API for put-call parity, synthetic forward pricing, and signal research.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    tickers: list[str] = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ"]
    scan_mode: str = "single"
    max_expiries_per_ticker: int = 1
    risk_free_rate: float = 0.05
    dividend_yield: float = 0.005
    stock_slippage_bps: float = 2.0
    min_net_edge: float = 0.05
    max_total_spread: float = 1.00
    min_open_interest: int = 500
    min_liquidity_score: int = 50
    min_edge_to_spread: float = 0.50
    min_total_spread_floor: float = 0.05
    max_moneyness_deviation: float = 0.20
    min_option_bid: float = 0.01
    save_snapshot: bool = False


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []

    output = df.copy()
    output = output.replace([float("inf"), float("-inf")], None)
    output = output.where(pd.notnull(output), None)

    return output.to_dict(orient="records")


def get_expiries_for_ticker(ticker: str, max_count: int) -> list[str]:
    stock = yf.Ticker(ticker)
    expiries = list(stock.options)

    if not expiries:
        return []

    return expiries[:max_count]


@app.get("/health")
def health():
    return {
        "status": "online",
        "engine": "put-call-parity",
        "mode": "research",
    }


@app.post("/scan")
def run_scan(request: ScanRequest):
    all_results = []
    errors = []

    cleaned_tickers = []

    for ticker in request.tickers:
        ticker_clean = ticker.strip().upper()

        if ticker_clean:
            cleaned_tickers.append(ticker_clean)

    cleaned_tickers = list(dict.fromkeys(cleaned_tickers))

    for ticker in cleaned_tickers:
        try:
            expiries = get_expiries_for_ticker(
                ticker=ticker,
                max_count=request.max_expiries_per_ticker,
            )

            if not expiries:
                errors.append(f"{ticker}: no option expiries found")
                continue

            if request.scan_mode.lower() == "single":
                expiries = expiries[:1]

            for expiry in expiries:
                df = scan_put_call_parity(
                    ticker=ticker,
                    expiry=expiry,
                    risk_free_rate=request.risk_free_rate,
                    dividend_yield=request.dividend_yield,
                    stock_slippage_bps=request.stock_slippage_bps,
                    min_net_edge=request.min_net_edge,
                    max_total_spread=request.max_total_spread,
                    min_open_interest=request.min_open_interest,
                    min_liquidity_score=request.min_liquidity_score,
                    min_edge_to_spread=request.min_edge_to_spread,
                    min_total_spread_floor=request.min_total_spread_floor,
                    max_moneyness_deviation=request.max_moneyness_deviation,
                    min_option_bid=request.min_option_bid,
                )

                if not df.empty:
                    all_results.append(df)

        except Exception as e:
            errors.append(f"{ticker}: {str(e)}")

    if not all_results:
        return {
            "summary": {
                "tickers": len(cleaned_tickers),
                "rows": 0,
                "research": 0,
                "watchlist": 0,
                "data_issues": 0,
                "no_trade": 0,
                "max_edge": 0,
                "avg_confidence": 0,
                "avg_liquidity": 0,
            },
            "rows": [],
            "errors": errors,
        }

    combined = pd.concat(all_results, ignore_index=True)

    signal_rank = {
        "Research candidate": 0,
        "Watchlist": 1,
        "Data quality issue": 2,
        "No trade": 3,
    }

    combined["signal_rank"] = combined["signal"].map(signal_rank).fillna(99)

    combined = combined.sort_values(
        ["signal_rank", "confidence_score", "executable_edge_after_costs"],
        ascending=[True, False, False],
    ).drop(columns=["signal_rank"])

    if request.save_snapshot:
        try:
            save_scan_snapshot(combined)
        except Exception as e:
            errors.append(f"snapshot error: {str(e)}")

    summary = {
        "tickers": len(cleaned_tickers),
        "rows": int(len(combined)),
        "research": int((combined["signal"] == "Research candidate").sum()),
        "watchlist": int((combined["signal"] == "Watchlist").sum()),
        "data_issues": int((combined["signal"] == "Data quality issue").sum()),
        "no_trade": int((combined["signal"] == "No trade").sum()),
        "max_edge": round(float(combined["executable_edge_after_costs"].max()), 4),
        "avg_confidence": round(float(combined["confidence_score"].mean()), 2),
        "avg_liquidity": round(float(combined["liquidity_score"].mean()), 2),
    }

    return {
        "summary": summary,
        "rows": dataframe_to_records(combined),
        "errors": errors,
    }


@app.get("/research/summary")
def research_summary():
    history_df = load_all_snapshots()

    if history_df.empty:
        return {
            "summary": {},
            "decay": [],
            "persistence": [],
        }

    summary = summarize_research_history(history_df)
    decay = signal_decay_analysis(history_df)
    persistence = signal_persistence_score(history_df)

    return {
        "summary": summary,
        "decay": dataframe_to_records(decay),
        "persistence": dataframe_to_records(persistence),
    }
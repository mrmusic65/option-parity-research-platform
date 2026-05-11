Kopiera allt nedan och ersätt hela `README.md`.

# Execution-Aware Options Relative Value Research Platform

A full-stack options research platform for analyzing put-call parity deviations, synthetic forward pricing, implied financing, execution-aware signal quality, Black-Scholes pricing, Greeks, and signal persistence over time.

The system combines a Python quantitative engine, a FastAPI backend, and a React frontend designed as an institutional-style options research terminal.

A research-first options analytics platform that turns put-call parity theory into an execution-aware workflow for synthetic forward diagnostics, signal filtering, trade diagnostics, Black-Scholes pricing, Greeks, and historical persistence analysis.

---

## Screenshot

<p align="center">
  <img src="screenshots/dashboard.png" alt="Dashboard" width="900">
</p>

---

## Tech Stack

* Python
* FastAPI
* React
* Vite
* Pandas
* NumPy
* yfinance
* Streamlit prototype
* Local CSV snapshot storage
* PowerShell quick-start script

---

## Overview

This project scans listed option chains across a user-defined equity universe and evaluates potential relative-value dislocations using put-call parity.

Core pricing relationship:

```
C - P = S * exp(-qT) - K * exp(-rT)
```

Where:

```
C = call option price
P = put option price
S = spot price
K = strike price
r = risk-free rate
q = dividend yield
T = time to expiration
```

The platform evaluates synthetic forward trades using execution-aware bid/ask logic:

```
Buy synthetic forward  = buy call at ask, sell put at bid
Sell synthetic forward = sell call at bid, buy put at ask
```

The goal is not to claim executable arbitrage from retail data. The goal is to build a disciplined research workflow for detecting, filtering, and studying potential options relative-value signals.

---

## Key Features

* Multi-ticker option chain scanning
* Put-call parity diagnostics
* Synthetic forward pricing
* Bid/ask-aware execution logic
* Implied financing rate estimation
* Implied dividend yield estimation
* Liquidity scoring
* Confidence scoring
* Data-quality filtering
* Moneyness filters
* Spread and open interest filters
* Snapshot logging
* Signal decay analysis
* Signal persistence scoring
* Research Lab for historical signal analysis
* Trade Diagnostics panel
* Black-Scholes theoretical option pricing
* Greeks calculation: Delta, Gamma, Vega, Theta, Rho
* d1 and d2 diagnostics
* Interactive Black-Scholes / Greeks panel in React
* React-based institutional dashboard
* FastAPI backend connected to the Python quant engine
* One-command Windows startup through start-dev.ps1

---

## Project Structure

```
option_parity_scanner/
│
├── scanner.py
│   Core quantitative engine for put-call parity, synthetic forward pricing,
│   implied financing, data-quality filters, liquidity scoring, and signal generation.
│
├── research.py
│   Research layer for saving snapshots, loading historical data,
│   signal decay analysis, persistence scoring, and research summaries.
│
├── option_math.py
│   Black-Scholes pricing and Greeks module.
│
├── app.py
│   Streamlit prototype used during early development.
│
├── backend/
│   ├── __init__.py
│   └── api.py
│       FastAPI backend exposing scanner, research, and Black-Scholes endpoints.
│
├── frontend/
│   React/Vite frontend dashboard.
│
├── screenshots/
│   Dashboard screenshots used in the README.
│
├── data_logs/
│   Local snapshot storage for research history.
│
├── requirements.txt
├── start-dev.ps1
├── .gitignore
└── README.md
```

---

## Architecture

```
React Frontend
      ↓
FastAPI Backend
      ↓
Python Quant Engine
      ↓
yfinance option-chain data
      ↓
Research snapshots and historical signal analysis
```

The frontend communicates with the backend through HTTP endpoints.

The backend calls the Python scanner, research modules, and Black-Scholes pricing module.

Snapshots are stored locally as CSV files for longitudinal signal analysis.

---

## Backend API

The backend exposes four primary endpoints:

```
GET /health
POST /scan
GET /research/summary
POST /black-scholes
```

---

### GET /health

Checks whether the backend is online.

Example response:

```
{
  "status": "online",
  "engine": "put-call-parity",
  "mode": "research",
  "modules": [
    "scanner",
    "research",
    "black-scholes",
    "greeks"
  ]
}
```

---

### POST /scan

Runs the options scanner for a given universe.

Example request:

```
{
  "tickers": ["AAPL", "MSFT", "NVDA"],
  "scan_mode": "single",
  "max_expiries_per_ticker": 1,
  "risk_free_rate": 0.05,
  "dividend_yield": 0.005,
  "stock_slippage_bps": 2.0,
  "min_net_edge": 0.05,
  "max_total_spread": 1.0,
  "min_open_interest": 500,
  "min_liquidity_score": 50,
  "min_edge_to_spread": 0.5,
  "min_total_spread_floor": 0.05,
  "max_moneyness_deviation": 0.2,
  "min_option_bid": 0.01,
  "save_snapshot": false
}
```

Example response structure:

```
{
  "summary": {
    "tickers": 3,
    "rows": 100,
    "research": 2,
    "watchlist": 5,
    "data_issues": 20,
    "no_trade": 73,
    "max_edge": 0.42,
    "avg_confidence": 74.2,
    "avg_liquidity": 68.9
  },
  "rows": [],
  "errors": []
}
```

---

### GET /research/summary

Loads historical snapshots and returns research analytics such as signal decay and persistence.

Example response structure:

```
{
  "summary": {
    "total_snapshots": 5,
    "total_rows": 300,
    "unique_tickers": 4,
    "research_candidates": 8,
    "watchlist": 15,
    "data_quality_issues": 40
  },
  "decay": [],
  "persistence": []
}
```

---

### POST /black-scholes

Calculates Black-Scholes theoretical option price and Greeks.

Example request:

```
{
  "option_type": "call",
  "spot": 100,
  "strike": 100,
  "time_to_expiry": 1,
  "risk_free_rate": 0.05,
  "dividend_yield": 0,
  "volatility": 0.2
}
```

Example response:

```
{
  "option_type": "call",
  "spot": 100,
  "strike": 100,
  "time_to_expiry": 1,
  "risk_free_rate": 0.05,
  "dividend_yield": 0,
  "volatility": 0.2,
  "price": 10.450584,
  "delta": 0.636831,
  "gamma": 0.018762,
  "vega": 0.37524,
  "theta": -0.017573,
  "rho": 0.532325,
  "d1": 0.35,
  "d2": 0.15
}
```

---

## Black-Scholes and Greeks Module

The platform includes a standalone Black-Scholes module for theoretical option pricing and Greeks.

The module calculates:

* Theoretical call and put prices
* Delta
* Gamma
* Vega
* Theta
* Rho
* d1
* d2

The calculation supports continuous dividend yield and is exposed through the FastAPI backend:

```
POST /black-scholes
```

The React frontend includes an interactive Black-Scholes Lab where users can adjust:

* Option type
* Spot price
* Strike price
* Time to expiration
* Risk-free rate
* Dividend yield
* Volatility

This expands the platform beyond put-call parity and synthetic forward diagnostics into broader options pricing and risk analysis.

---

## How to Run

### Quick Start on Windows

From the project root:

```
.\start-dev.ps1
```

This starts both the FastAPI backend and the React frontend, then opens the dashboard in the browser.

---

### Manual Setup

### 1. Clone the repository

```
git clone <your-repo-url>
cd option_parity_scanner
```

### 2. Create and activate a Python virtual environment

Windows PowerShell:

```
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python dependencies

```
pip install -r requirements.txt
```

### 4. Start the backend

From the project root:

```
uvicorn backend.api:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

API documentation:

```
http://127.0.0.1:8000/docs
```

### 5. Start the frontend

Open a second terminal:

```
cd frontend
npm install
npm run dev
```

Frontend:

```
http://localhost:5173
```

---

## Streamlit Prototype

The project also includes the original Streamlit prototype:

```
streamlit run app.py
```

The Streamlit version was used to prototype the research workflow before building the React/FastAPI full-stack version.

The main application is now the React/FastAPI version.

---

## Research Workflow

The intended workflow is:

```
1. Define universe
2. Adjust research filters
3. Run live option-chain scan
4. Rank synthetic forward parity signals
5. Inspect trade diagnostics
6. Save research snapshot
7. Load Research Lab
8. Analyze signal decay and persistence
9. Use Black-Scholes Lab for pricing and Greeks diagnostics
```

This workflow is designed to separate one-off noisy market data from recurring signal behavior.

---

## Important Limitations

This project uses publicly available option-chain data through yfinance.

The output should not be interpreted as directly executable arbitrage.

Important limitations include:

* Delayed or stale option quotes
* Wide bid/ask spreads
* Incomplete open interest or volume data
* Dividend assumptions may be simplified
* Borrow costs are not modeled
* Early exercise risk is not fully modeled
* Execution latency is not modeled
* Transaction costs may be underestimated
* Professional market data would be required for production use

The platform should be viewed as a research tool, not an automated trading system.

---

## Why This Project Matters

Put-call parity is a foundational no-arbitrage relationship in options pricing.

In real markets, that relationship is affected by bid/ask spreads, liquidity constraints, dividends, funding costs, borrow costs, execution risk, and quote quality.

This project turns a theoretical pricing relationship into an execution-aware research workflow.

It does not simply search for apparent mispricing. It attempts to classify whether a signal is potentially meaningful, liquid, persistent, and worth further research.

The Black-Scholes and Greeks module expands the platform into broader options pricing and risk analysis, making it more than a parity scanner.

---

## Future Improvements

Potential next steps:

* Connect to professional options data
* Add real dividend schedule handling
* Add borrow-cost assumptions
* Add volatility surface diagnostics
* Add implied volatility solver
* Add volatility smile and skew visualization
* Add historical options database
* Add Greeks directly to scanner output
* Add user-controlled filters for all backend parameters
* Add authentication
* Add Docker setup
* Add automated tests
* Add deployment configuration
* Add broker/paper-trading integration for execution simulation

---

## Positioning

This project is best described as:

```
An execution-aware options relative-value research platform.
```

Not:

```
A guaranteed arbitrage scanner.
```

The goal is to demonstrate quantitative research thinking, derivatives knowledge, options market structure awareness, full-stack engineering ability, and disciplined handling of noisy financial data.

---

## CV Description

Developed a full-stack options research platform with Python, FastAPI and React for execution-aware put-call parity analysis, synthetic forward pricing, Black-Scholes pricing, Greeks, trade diagnostics, and signal persistence using real option-chain data.

---

## Longer Project Description

Built a full-stack options relative-value research platform using Python, FastAPI, React, and real option-chain data. The system scans multi-ticker option chains for put-call parity deviations and synthetic forward mispricing, applies bid/ask-aware execution logic, liquidity and data-quality filters, estimates implied financing and dividend signals, stores research snapshots, analyzes signal decay and persistence over time, and includes a Black-Scholes / Greeks module for theoretical pricing and risk diagnostics.

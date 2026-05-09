import streamlit as st
import pandas as pd
import plotly.express as px

from scanner import scan_put_call_parity

from research import (
    save_scan_snapshot,
    load_all_snapshots,
    summarize_research_history,
    signal_summary_by_ticker,
    edge_summary_by_ticker,
    time_series_signal_counts,
    signal_decay_analysis,
    signal_persistence_score,
)

try:
    from research import signal_quality_dashboard
except ImportError:
    signal_quality_dashboard = None

try:
    from research import signal_transition_matrix, edge_half_life_analysis
except ImportError:
    signal_transition_matrix = None
    edge_half_life_analysis = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Options Relative Value Terminal",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# INSTITUTIONAL TERMINAL CSS
# ============================================================

def inject_terminal_css():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(34,197,94,0.11), transparent 28%),
                radial-gradient(circle at top right, rgba(59,130,246,0.11), transparent 24%),
                linear-gradient(180deg, #050B14 0%, #07111F 55%, #081221 100%);
        }

        .block-container {
            max-width: 1560px;
            padding-top: 1.1rem;
            padding-bottom: 2.5rem;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #070E1A 0%, #0E1726 100%);
            border-right: 1px solid rgba(148,163,184,0.14);
        }

        .terminal-hero {
            padding: 1.25rem 1.45rem;
            border: 1px solid rgba(34,197,94,0.22);
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(2,6,23,0.97), rgba(15,23,42,0.90)),
                repeating-linear-gradient(
                    0deg,
                    rgba(255,255,255,0.018),
                    rgba(255,255,255,0.018) 1px,
                    transparent 1px,
                    transparent 3px
                );
            box-shadow:
                0 12px 38px rgba(0,0,0,0.34),
                inset 0 0 34px rgba(34,197,94,0.035);
            margin-bottom: 1rem;
        }

        .terminal-kicker {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: #22C55E;
            font-size: 0.76rem;
            font-weight: 850;
            letter-spacing: 0.11rem;
            margin-bottom: 0.28rem;
        }

        .terminal-title {
            font-size: 2.18rem;
            font-weight: 820;
            color: #F8FAFC;
            letter-spacing: -0.055rem;
            margin-bottom: 0.25rem;
        }

        .terminal-subtitle {
            font-size: 0.94rem;
            color: #94A3B8;
            line-height: 1.52;
            max-width: 1060px;
            margin-bottom: 0.8rem;
        }

        .terminal-status-box {
            text-align: right;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: #94A3B8;
            font-size: 0.76rem;
            line-height: 1.65;
            min-width: 175px;
        }

        .status-good {
            color: #22C55E;
            font-weight: 850;
        }

        .status-blue {
            color: #60A5FA;
            font-weight: 850;
        }

        .terminal-pill {
            display: inline-block;
            padding: 0.34rem 0.68rem;
            border-radius: 999px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.72rem;
            font-weight: 850;
            letter-spacing: 0.04rem;
            margin-right: 0.42rem;
            margin-top: 0.22rem;
        }

        .pill-green {
            background: rgba(34,197,94,0.10);
            color: #22C55E;
            border: 1px solid rgba(34,197,94,0.32);
        }

        .pill-blue {
            background: rgba(59,130,246,0.11);
            color: #60A5FA;
            border: 1px solid rgba(59,130,246,0.32);
        }

        .pill-purple {
            background: rgba(168,85,247,0.11);
            color: #C084FC;
            border: 1px solid rgba(168,85,247,0.32);
        }

        .terminal-strip {
            background: rgba(2, 6, 23, 0.88);
            border: 1px solid rgba(34,197,94,0.22);
            border-radius: 14px;
            padding: 0.78rem 1rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: #22C55E;
            font-size: 0.82rem;
            margin-bottom: 1rem;
            box-shadow: inset 0 0 18px rgba(34,197,94,0.04);
            overflow-x: auto;
            white-space: nowrap;
        }

        .terminal-card {
            background:
                linear-gradient(180deg, rgba(2,6,23,0.94), rgba(15,23,42,0.90));
            border: 1px solid rgba(51,65,85,0.95);
            border-radius: 18px;
            padding: 1rem 1rem 0.95rem 1rem;
            box-shadow: 0 10px 32px rgba(0,0,0,0.30);
            margin-bottom: 1rem;
        }

        .terminal-label {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: #64748B;
            font-size: 0.70rem;
            letter-spacing: 0.09rem;
            font-weight: 850;
            text-transform: uppercase;
            margin-bottom: 0.28rem;
        }

        .terminal-value {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: #F8FAFC;
            font-size: 1.02rem;
            font-weight: 800;
            line-height: 1.45;
        }

        .terminal-green {
            color: #22C55E;
        }

        .terminal-blue {
            color: #60A5FA;
        }

        .terminal-amber {
            color: #F59E0B;
        }

        .terminal-red {
            color: #F87171;
        }

        .section-title {
            font-size: 1.07rem;
            font-weight: 820;
            color: #F8FAFC;
            margin-top: 0.25rem;
            margin-bottom: 0.35rem;
            letter-spacing: -0.01rem;
        }

        .section-subtitle {
            font-size: 0.86rem;
            color: #94A3B8;
            margin-bottom: 0.85rem;
        }

        .subterminal-title {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.83rem;
            font-weight: 850;
            color: #22C55E;
            letter-spacing: 0.07rem;
            margin-bottom: 0.65rem;
        }

        .panel-card {
            padding: 1rem 1rem 0.85rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(148,163,184,0.16);
            background: rgba(15,23,42,0.72);
            box-shadow: 0 8px 28px rgba(0,0,0,0.20);
            margin-bottom: 1rem;
        }

        .small-note {
            color: #94A3B8;
            font-size: 0.82rem;
            margin-bottom: 0.6rem;
        }

        div[data-testid="stMetric"] {
            background:
                linear-gradient(180deg, rgba(15,23,42,0.96), rgba(15,23,42,0.84));
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            box-shadow: 0 6px 22px rgba(0,0,0,0.22);
        }

        div[data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-weight: 750;
        }

        div[data-testid="stMetricValue"] {
            color: #F8FAFC !important;
            font-weight: 850;
        }

        div[data-testid="stMetricDelta"] {
            color: #22C55E !important;
        }

        div.stButton > button,
        div[data-testid="stDownloadButton"] > button {
            background: linear-gradient(135deg, #16A34A, #2563EB);
            color: white;
            border: 0;
            border-radius: 12px;
            font-weight: 850;
            min-height: 2.75rem;
            box-shadow: 0 8px 24px rgba(37,99,235,0.20);
        }

        div.stButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            background: linear-gradient(135deg, #22C55E, #3B82F6);
            color: white;
            border: 0;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 14px;
            overflow: hidden;
        }

        button[role="tab"] {
            font-weight: 850;
            border-radius: 12px 12px 0 0;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            letter-spacing: 0.02rem;
        }

        hr {
            border-color: rgba(148,163,184,0.14);
            margin-top: 1.35rem;
            margin-bottom: 1.35rem;
        }

        .stAlert {
            border-radius: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_terminal_css()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="terminal-hero">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">
            <div>
                <div class="terminal-kicker">OPTIONS RELATIVE VALUE TERMINAL</div>
                <div class="terminal-title">Synthetic Forward & Parity Research Desk</div>
                <div class="terminal-subtitle">
                    Multi-ticker option-chain diagnostics for put-call parity, implied financing,
                    bid/ask-aware synthetic forwards, data-quality validation, signal decay and persistence research.
                </div>
            </div>
            <div class="terminal-status-box">
                <div>MODE: <span class="status-good">RESEARCH</span></div>
                <div>ENGINE: <span class="status-blue">PARITY</span></div>
                <div>DATA: YFINANCE</div>
                <div>STATUS: <span class="status-good">LIVE</span></div>
            </div>
        </div>

        <div style="margin-top:0.72rem;">
            <span class="terminal-pill pill-green">LIVE CHAIN SCAN</span>
            <span class="terminal-pill pill-blue">SYNTHETIC FORWARD</span>
            <span class="terminal-pill pill-purple">EXECUTION FILTERS</span>
            <span class="terminal-pill pill-green">SIGNAL DECAY</span>
            <span class="terminal-pill pill-blue">PERSISTENCE ENGINE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Model Controls")

with st.sidebar.expander("Universe", expanded=True):
    ticker_input = st.text_area(
        "Tickers",
        value="AAPL, MSFT, NVDA, TSLA, SPY, QQQ",
        help="Enter one or more tickers separated by commas.",
    )

    scan_mode = st.radio(
        "Scan mode",
        ["Single expiry per ticker", "All available expiries"],
        index=0,
    )

    max_expiries_per_ticker = st.number_input(
        "Max expiries per ticker",
        value=1,
        min_value=1,
        max_value=10,
        step=1,
    )

with st.sidebar.expander("Pricing Assumptions", expanded=True):
    risk_free_rate = st.number_input(
        "Risk-free rate",
        value=0.05,
        step=0.005,
        format="%.4f",
    )

    dividend_yield = st.number_input(
        "Default dividend yield",
        value=0.005,
        step=0.001,
        format="%.4f",
    )

    stock_slippage_bps = st.number_input(
        "Stock slippage/cost (bps)",
        value=2.0,
        step=0.5,
        format="%.1f",
    )

with st.sidebar.expander("Execution & Research Filters", expanded=True):
    min_net_edge = st.number_input(
        "Minimum net edge after costs",
        value=0.05,
        step=0.01,
        format="%.2f",
    )

    max_total_spread = st.number_input(
        "Maximum total option spread",
        value=1.00,
        step=0.10,
        format="%.2f",
    )

    min_open_interest = st.number_input(
        "Minimum total open interest",
        value=500,
        step=100,
    )

    min_liquidity_score = st.number_input(
        "Minimum liquidity score",
        value=50,
        step=5,
    )

    min_edge_to_spread = st.number_input(
        "Minimum edge/spread ratio",
        value=0.50,
        step=0.10,
        format="%.2f",
    )

    min_total_spread_floor = st.number_input(
        "Minimum spread floor",
        value=0.05,
        step=0.01,
        format="%.2f",
    )

    max_moneyness_deviation = st.number_input(
        "Max moneyness deviation",
        value=0.20,
        step=0.05,
        format="%.2f",
    )

    min_option_bid = st.number_input(
        "Minimum option bid",
        value=0.01,
        step=0.01,
        format="%.2f",
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_tickers(raw_text: str) -> list[str]:
    tickers = [
        t.strip().upper()
        for t in raw_text.replace("\n", ",").split(",")
        if t.strip()
    ]
    return list(dict.fromkeys(tickers))


def compact_view(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "ticker",
        "expiry",
        "strike",
        "moneyness",
        "spot",
        "best_trade",
        "executable_edge_after_costs",
        "edge_to_spread",
        "confidence_score",
        "liquidity_score",
        "total_spread",
        "total_oi",
        "data_quality",
        "implied_rate_mid",
        "implied_dividend_yield_mid",
        "signal",
        "market_diagnostic",
        "risk_note",
    ]
    existing_columns = [col for col in columns if col in df.columns]
    return df[existing_columns].copy()


def explain_trade(row: pd.Series) -> str:
    if row.get("best_trade") == "Buy synthetic forward":
        return (
            "The scanner indicates that the synthetic forward may be cheap relative "
            "to theoretical parity. The execution-aware test assumes buying the call "
            "at ask and selling the put at bid."
        )

    return (
        "The scanner indicates that the synthetic forward may be rich relative "
        "to theoretical parity. The execution-aware test assumes selling the call "
        "at bid and buying the put at ask."
    )


def get_expiries_for_ticker(ticker: str, max_count: int) -> list[str]:
    import yfinance as yf

    stock = yf.Ticker(ticker)
    expiries = list(stock.options)

    if not expiries:
        return []

    return expiries[:max_count]


def run_multi_ticker_scan(tickers: list[str]) -> tuple[pd.DataFrame, list[str]]:
    all_results = []
    errors = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_jobs = max(len(tickers), 1)
    completed_jobs = 0

    for ticker in tickers:
        try:
            expiries = get_expiries_for_ticker(
                ticker,
                int(max_expiries_per_ticker),
            )

            if not expiries:
                errors.append(f"{ticker}: no option expiries found")
                completed_jobs += 1
                progress_bar.progress(completed_jobs / total_jobs)
                continue

            if scan_mode == "Single expiry per ticker":
                expiries = expiries[:1]

            for expiry in expiries:
                status_text.write(f"Scanning {ticker} | {expiry}")

                df = scan_put_call_parity(
                    ticker=ticker,
                    expiry=expiry,
                    risk_free_rate=risk_free_rate,
                    dividend_yield=dividend_yield,
                    stock_slippage_bps=stock_slippage_bps,
                    min_net_edge=min_net_edge,
                    max_total_spread=max_total_spread,
                    min_open_interest=min_open_interest,
                    min_liquidity_score=min_liquidity_score,
                    min_edge_to_spread=min_edge_to_spread,
                    min_total_spread_floor=min_total_spread_floor,
                    max_moneyness_deviation=max_moneyness_deviation,
                    min_option_bid=min_option_bid,
                )

                if not df.empty:
                    all_results.append(df)

        except Exception as e:
            errors.append(f"{ticker}: {e}")

        completed_jobs += 1
        progress_bar.progress(completed_jobs / total_jobs)

    status_text.write("Scan complete.")

    if not all_results:
        return pd.DataFrame(), errors

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

    return combined, errors


def plot_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    height: int = 330,
):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info("No chart data available.")
        return

    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        template="plotly_dark",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        margin=dict(l=20, r=20, t=45, b=35),
        height=height,
    )

    fig.update_xaxes(gridcolor="rgba(148,163,184,0.12)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.12)")

    st.plotly_chart(fig, use_container_width=True)


def plot_line(
    df: pd.DataFrame,
    x: str,
    y_columns: list[str],
    title: str,
    height: int = 330,
):
    if df.empty or x not in df.columns:
        st.info("No time series data available.")
        return

    fig = px.line(
        df,
        x=x,
        y=y_columns,
        title=title,
        template="plotly_dark",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        margin=dict(l=20, r=20, t=45, b=35),
        height=height,
    )

    fig.update_xaxes(gridcolor="rgba(148,163,184,0.12)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.12)")

    st.plotly_chart(fig, use_container_width=True)


def safe_max(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(df[col].max())


def safe_mean(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(df[col].mean())


# ============================================================
# MAIN STATE
# ============================================================

tickers = parse_tickers(ticker_input)

tabs = st.tabs(
    [
        "COMMAND CENTER",
        "SIGNAL MATRIX",
        "RESEARCH LAB",
        "TRADE DIAGNOSTICS",
        "MODEL NOTES",
    ]
)


# ============================================================
# TAB 1: COMMAND CENTER
# ============================================================

with tabs[0]:
    st.markdown(
        f"""
        <div class="terminal-strip">
            &gt; LOAD UNIVERSE: {", ".join(tickers)}
            &nbsp;&nbsp;|&nbsp;&nbsp;
            ENGINE: PUT-CALL PARITY
            &nbsp;&nbsp;|&nbsp;&nbsp;
            MODE: EXECUTION-AWARE
            &nbsp;&nbsp;|&nbsp;&nbsp;
            STATUS: READY
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([3.2, 1])

    with top_left:
        st.markdown(
            '<div class="section-title">Command Center</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-subtitle">Institutional overview for live parity scans, signal triage and research workflow control.</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="terminal-card">
                <div class="terminal-label">Active Universe</div>
                <div class="terminal-value terminal-blue">{", ".join(tickers)}</div>
                <br>
                <div class="terminal-label">Scan Protocol</div>
                <div class="terminal-value">
                    Synthetic forward parity check · bid/ask execution · liquidity scoring · data-quality validation
                </div>
                <br>
                <div class="terminal-label">Research Objective</div>
                <div class="terminal-value terminal-green">
                    Detect repeatable relative-value dislocations, not one-off stale quote artifacts.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_right:
        st.markdown("<br>", unsafe_allow_html=True)

        run_scan = st.button(
            "RUN LIVE SCAN",
            type="primary",
            use_container_width=True,
        )

        st.markdown(
            """
            <div class="terminal-card">
                <div class="terminal-label">System State</div>
                <div class="terminal-value terminal-green">READY</div>
                <br>
                <div class="terminal-label">Sidebar</div>
                <div class="terminal-value terminal-amber">Collapsed by default</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if run_scan:
        if not tickers:
            st.error("Please enter at least one ticker.")
            st.stop()

        df, errors = run_multi_ticker_scan(tickers)

        st.session_state["scanner_df"] = df
        st.session_state["scanner_errors"] = errors

    if "scanner_df" not in st.session_state:
        st.info("Run a live scan to populate the terminal.")
    else:
        df = st.session_state["scanner_df"]
        errors = st.session_state.get("scanner_errors", [])

        if df.empty:
            st.warning("No valid option pairs found across the selected universe.")

            if errors:
                with st.expander("Scan warnings / errors"):
                    for error in errors:
                        st.write(f"- {error}")

            st.stop()

        research_candidates = df[df["signal"] == "Research candidate"]
        watchlist = df[df["signal"] == "Watchlist"]
        data_quality = df[df["signal"] == "Data quality issue"]
        no_trade = df[df["signal"] == "No trade"]

        max_edge = safe_max(df, "executable_edge_after_costs")
        avg_confidence = safe_mean(df, "confidence_score")
        avg_liquidity = safe_mean(df, "liquidity_score")

        k1, k2, k3, k4, k5, k6 = st.columns(6)

        k1.metric("UNIVERSE", len(tickers))
        k2.metric("ROWS", len(df))
        k3.metric("RESEARCH", len(research_candidates))
        k4.metric("WATCHLIST", len(watchlist))
        k5.metric("DATA ISSUES", len(data_quality))
        k6.metric("MAX EDGE", round(max_edge, 4))

        k7, k8, k9, k10 = st.columns(4)

        k7.metric("AVG CONFIDENCE", round(avg_confidence, 2))
        k8.metric("AVG LIQUIDITY", round(avg_liquidity, 2))
        k9.metric("NO TRADE", len(no_trade))
        k10.metric("SCAN MODE", scan_mode)

        if errors:
            with st.expander("Scan warnings / errors"):
                for error in errors:
                    st.write(f"- {error}")

        st.divider()

        left, right = st.columns([1.55, 1])

        with left:
            st.markdown(
                '<div class="subterminal-title">TOP RESEARCH SIGNALS</div>',
                unsafe_allow_html=True,
            )

            combined_top = pd.concat([research_candidates, watchlist]).copy()

            if combined_top.empty:
                st.info("No research or watchlist candidates under current filters.")
            else:
                st.dataframe(
                    compact_view(combined_top.head(20)),
                    use_container_width=True,
                    hide_index=True,
                    height=360,
                )

        with right:
            st.markdown(
                '<div class="subterminal-title">SIGNAL DISTRIBUTION</div>',
                unsafe_allow_html=True,
            )

            signal_dist = (
                df.groupby("signal")
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )

            plot_bar(
                signal_dist,
                x="signal",
                y="count",
                title="Signal Distribution",
                height=360,
            )

        st.divider()

        chart_df = df.sort_values(
            "executable_edge_after_costs",
            ascending=False,
        ).head(15).copy()

        if not chart_df.empty:
            chart_df["label"] = (
                chart_df["ticker"] + " K=" + chart_df["strike"].astype(str)
            )

        plot_bar(
            chart_df,
            x="label",
            y="executable_edge_after_costs",
            title="Top 15 Net Edge by Ticker / Strike",
            height=360,
        )

        st.divider()

        st.markdown(
            '<div class="subterminal-title">EXPORT / SNAPSHOT</div>',
            unsafe_allow_html=True,
        )

        csv = df.to_csv(index=False).encode("utf-8")

        ex1, ex2 = st.columns(2)

        with ex1:
            st.download_button(
                label="Download Current Scan CSV",
                data=csv,
                file_name="put_call_parity_scanner_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with ex2:
            if st.button("Save Research Snapshot", use_container_width=True):
                try:
                    saved_path = save_scan_snapshot(df)
                    st.success(f"Snapshot saved to {saved_path}")
                except Exception as e:
                    st.error(f"Could not save snapshot: {e}")


# ============================================================
# TAB 2: SIGNAL MATRIX
# ============================================================

with tabs[1]:
    st.markdown(
        '<div class="section-title">Signal Matrix</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Filter, rank and inspect synthetic forward parity dislocations across the live universe.</div>',
        unsafe_allow_html=True,
    )

    if "scanner_df" not in st.session_state or st.session_state["scanner_df"].empty:
        st.info("Run a scan first to populate the Signal Matrix.")
    else:
        df = st.session_state["scanner_df"].copy()

        f1, f2, f3, f4 = st.columns(4)

        selected_signal = f1.selectbox(
            "Signal",
            ["All"] + sorted(df["signal"].dropna().unique().tolist()),
        )

        selected_ticker = f2.selectbox(
            "Ticker",
            ["All"] + sorted(df["ticker"].dropna().unique().tolist()),
        )

        selected_trade = f3.selectbox(
            "Best trade",
            ["All"] + sorted(df["best_trade"].dropna().unique().tolist())
            if "best_trade" in df.columns
            else ["All"],
        )

        min_edge_filter = f4.number_input(
            "Min net edge",
            value=0.0,
            step=0.01,
            format="%.2f",
        )

        filtered_df = df.copy()

        if selected_signal != "All":
            filtered_df = filtered_df[filtered_df["signal"] == selected_signal]

        if selected_ticker != "All":
            filtered_df = filtered_df[filtered_df["ticker"] == selected_ticker]

        if "best_trade" in filtered_df.columns and selected_trade != "All":
            filtered_df = filtered_df[filtered_df["best_trade"] == selected_trade]

        filtered_df = filtered_df[
            filtered_df["executable_edge_after_costs"] >= min_edge_filter
        ]

        st.dataframe(
            compact_view(filtered_df),
            use_container_width=True,
            hide_index=True,
            height=560,
        )

        st.divider()

        st.markdown(
            '<div class="subterminal-title">MARKET DIAGNOSTICS</div>',
            unsafe_allow_html=True,
        )

        diagnostic_columns = [
            "ticker",
            "expiry",
            "strike",
            "implied_rate_mid",
            "implied_dividend_yield_mid",
            "edge_to_spread",
            "data_quality",
            "market_diagnostic",
            "signal",
        ]

        existing_diag_cols = [
            col for col in diagnostic_columns if col in df.columns
        ]

        st.dataframe(
            df[existing_diag_cols].head(100),
            use_container_width=True,
            hide_index=True,
            height=400,
        )


# ============================================================
# TAB 3: RESEARCH LAB
# ============================================================

with tabs[2]:
    st.markdown(
        '<div class="section-title">Research Lab</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Snapshot history, signal decay, persistence scoring, transition analysis and research diagnostics.</div>',
        unsafe_allow_html=True,
    )

    history_df = load_all_snapshots()

    if history_df.empty:
        st.info(
            "No saved scan snapshots yet. Save a snapshot from Command Center to start building the research dataset."
        )
    else:
        summary = summarize_research_history(history_df)

        r1, r2, r3, r4, r5, r6 = st.columns(6)

        r1.metric("SNAPSHOTS", summary["total_snapshots"])
        r2.metric("ROWS", summary["total_rows"])
        r3.metric("TICKERS", summary["unique_tickers"])
        r4.metric("RESEARCH", summary["research_candidates"])
        r5.metric("WATCHLIST", summary["watchlist"])
        r6.metric("DATA ISSUES", summary["data_quality_issues"])

        st.divider()

        if signal_quality_dashboard is not None:
            st.markdown(
                '<div class="subterminal-title">SIGNAL QUALITY DASHBOARD</div>',
                unsafe_allow_html=True,
            )

            quality = signal_quality_dashboard(history_df)

            def metric_from_row(row, metric_name):
                if row is None:
                    return "N/A", "N/A"

                label = f"{row['ticker']} | K={row['strike']}"
                value = row[metric_name]

                return value, label

            hp_value, hp_label = metric_from_row(
                quality["highest_persistence"],
                "persistence_score",
            )

            edge_value, edge_label = metric_from_row(
                quality["best_avg_edge"],
                "avg_edge",
            )

            recurring_value, recurring_label = metric_from_row(
                quality["most_recurring"],
                "recurrence_rate",
            )

            q1, q2, q3 = st.columns(3)

            q1.metric("Highest Persistence", hp_value, hp_label)
            q2.metric("Best Avg Edge", edge_value, edge_label)
            q3.metric("Most Recurring", recurring_value, recurring_label)

            st.divider()

        ts_counts = time_series_signal_counts(history_df)

        st.markdown(
            '<div class="subterminal-title">SIGNAL ACTIVITY OVER TIME</div>',
            unsafe_allow_html=True,
        )

        if not ts_counts.empty:
            st.dataframe(
                ts_counts,
                use_container_width=True,
                hide_index=True,
                height=200,
            )

            y_cols = [col for col in ts_counts.columns if col != "scan_date"]

            plot_line(
                ts_counts,
                x="scan_date",
                y_columns=y_cols,
                title="Signal Counts Over Time",
                height=340,
            )

        st.divider()

        left, right = st.columns(2)

        with left:
            st.markdown(
                '<div class="subterminal-title">CROSS-TICKER SIGNAL SUMMARY</div>',
                unsafe_allow_html=True,
            )

            ticker_signal_summary = signal_summary_by_ticker(history_df)

            if not ticker_signal_summary.empty:
                st.dataframe(
                    ticker_signal_summary,
                    use_container_width=True,
                    hide_index=True,
                    height=330,
                )

        with right:
            st.markdown(
                '<div class="subterminal-title">EDGE BEHAVIOR BY TICKER</div>',
                unsafe_allow_html=True,
            )

            ticker_edge_summary = edge_summary_by_ticker(history_df)

            if not ticker_edge_summary.empty:
                st.dataframe(
                    ticker_edge_summary,
                    use_container_width=True,
                    hide_index=True,
                    height=330,
                )

        st.divider()

        st.markdown(
            '<div class="subterminal-title">SIGNAL DECAY</div>',
            unsafe_allow_html=True,
        )

        decay_df = signal_decay_analysis(history_df)

        if decay_df.empty:
            st.info(
                "Not enough repeated observations yet. Save multiple snapshots of the same ticker/expiry/strike."
            )
        else:
            st.dataframe(
                decay_df.head(40),
                use_container_width=True,
                hide_index=True,
                height=340,
            )

            top_decay = decay_df.sort_values(
                "edge_decay",
                ascending=False,
            ).head(15).copy()

            if not top_decay.empty:
                top_decay["label"] = (
                    top_decay["ticker"] + " K=" + top_decay["strike"].astype(str)
                )

            plot_bar(
                top_decay,
                x="label",
                y="edge_decay",
                title="Top Signal Decay",
                height=330,
            )

        st.divider()

        st.markdown(
            '<div class="subterminal-title">SIGNAL PERSISTENCE</div>',
            unsafe_allow_html=True,
        )

        persistence_df = signal_persistence_score(history_df)

        if persistence_df.empty:
            st.info("Not enough historical observations yet to calculate persistence scores.")
        else:
            st.dataframe(
                persistence_df.head(40),
                use_container_width=True,
                hide_index=True,
                height=360,
            )

            top_persistence = persistence_df.head(15).copy()

            top_persistence["label"] = (
                top_persistence["ticker"] + " K=" + top_persistence["strike"].astype(str)
            )

            plot_bar(
                top_persistence,
                x="label",
                y="persistence_score",
                title="Top Persistence Scores",
                height=330,
            )

        if signal_transition_matrix is not None:
            st.divider()

            st.markdown(
                '<div class="subterminal-title">SIGNAL TRANSITION MATRIX</div>',
                unsafe_allow_html=True,
            )

            transition_df = signal_transition_matrix(history_df)

            if transition_df.empty:
                st.info("Not enough repeated observations yet to calculate signal transitions.")
            else:
                st.dataframe(
                    transition_df,
                    use_container_width=True,
                    hide_index=True,
                    height=260,
                )

        if edge_half_life_analysis is not None:
            st.divider()

            st.markdown(
                '<div class="subterminal-title">EDGE HALF-LIFE</div>',
                unsafe_allow_html=True,
            )

            half_life_df = edge_half_life_analysis(history_df)

            if half_life_df.empty:
                st.info("Not enough positive repeated edge observations yet to estimate half-life.")
            else:
                st.dataframe(
                    half_life_df.head(40),
                    use_container_width=True,
                    hide_index=True,
                    height=340,
                )

                chart_half_life = half_life_df[
                    half_life_df["half_life_reached"] == True
                ].head(15).copy()

                if not chart_half_life.empty:
                    chart_half_life["label"] = (
                        chart_half_life["ticker"]
                        + " K="
                        + chart_half_life["strike"].astype(str)
                    )

                plot_bar(
                    chart_half_life,
                    x="label",
                    y="half_life_hours",
                    title="Reached Half-Life in Hours",
                    height=330,
                )

        with st.expander("Show full historical research dataset"):
            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True,
                height=500,
            )


# ============================================================
# TAB 4: TRADE DIAGNOSTICS
# ============================================================

with tabs[3]:
    st.markdown(
        '<div class="section-title">Trade Diagnostics</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Single-candidate diagnostic panel for desk-style review and execution validation.</div>',
        unsafe_allow_html=True,
    )

    if "scanner_df" not in st.session_state or st.session_state["scanner_df"].empty:
        st.info("Run a scan first to inspect trade diagnostics.")
    else:
        df = st.session_state["scanner_df"].copy()

        candidate_df = df[
            df["signal"].isin(["Research candidate", "Watchlist"])
        ].copy()

        if candidate_df.empty:
            st.info("No research or watchlist candidates available for detailed review.")
        else:
            candidate_df["label"] = (
                candidate_df["ticker"]
                + " | "
                + candidate_df["expiry"]
                + " | K="
                + candidate_df["strike"].astype(str)
                + " | "
                + candidate_df["signal"]
            )

            selected_label = st.selectbox(
                "Select candidate",
                candidate_df["label"].tolist(),
            )

            row = candidate_df[candidate_df["label"] == selected_label].iloc[0]

            t1, t2, t3, t4, t5 = st.columns(5)

            t1.metric("Ticker", row["ticker"])
            t2.metric("Strike", row["strike"])
            t3.metric("Signal", row["signal"])
            t4.metric("Best Trade", row["best_trade"])
            t5.metric("Net Edge", row["executable_edge_after_costs"])

            st.divider()

            left, right = st.columns(2)

            with left:
                st.markdown(
                    '<div class="subterminal-title">TRADE SUMMARY</div>',
                    unsafe_allow_html=True,
                )

                st.write(f"Expiry: `{row.get('expiry', 'N/A')}`")
                st.write(f"Spot: `{row.get('spot', 'N/A')}`")
                st.write(f"Moneyness: `{row.get('moneyness', 'N/A')}`")
                st.write(f"Call bid / ask: `{row.get('call_bid', 'N/A')}` / `{row.get('call_ask', 'N/A')}`")
                st.write(f"Put bid / ask: `{row.get('put_bid', 'N/A')}` / `{row.get('put_ask', 'N/A')}`")
                st.write(f"Total spread: `{row.get('total_spread', 'N/A')}`")
                st.write(f"Total open interest: `{row.get('total_oi', 'N/A')}`")
                st.write(f"Liquidity score: `{row.get('liquidity_score', 'N/A')}`")
                st.write(f"Confidence score: `{row.get('confidence_score', 'N/A')}`")

            with right:
                st.markdown(
                    '<div class="subterminal-title">PARITY BREAKDOWN</div>',
                    unsafe_allow_html=True,
                )

                st.write(f"Dividend-adjusted spot: `{row.get('dividend_adjusted_spot', 'N/A')}`")
                st.write(f"PV(strike): `{row.get('pv_strike', 'N/A')}`")
                st.write(f"Theoretical parity: `{row.get('theoretical_parity', 'N/A')}`")
                st.write(f"Mid market parity: `{row.get('mid_market_parity', 'N/A')}`")
                st.write(f"Mid mispricing: `{row.get('mid_mispricing', 'N/A')}`")
                st.write(f"Implied rate: `{row.get('implied_rate_mid', 'N/A')}`")
                st.write(f"Implied dividend yield: `{row.get('implied_dividend_yield_mid', 'N/A')}`")
                st.write(f"Data quality: `{row.get('data_quality', 'N/A')}`")

            st.divider()

            e1, e2 = st.columns(2)

            with e1:
                st.markdown(
                    '<div class="subterminal-title">EXECUTION LOGIC</div>',
                    unsafe_allow_html=True,
                )

                st.write(explain_trade(row))
                st.write(f"Long synthetic cost: `{row.get('long_synth_cost', 'N/A')}`")
                st.write(f"Long synthetic edge after costs: `{row.get('long_synth_edge_after_costs', 'N/A')}`")
                st.write(f"Short synthetic credit: `{row.get('short_synth_credit', 'N/A')}`")
                st.write(f"Short synthetic edge after costs: `{row.get('short_synth_edge_after_costs', 'N/A')}`")

            with e2:
                st.markdown(
                    '<div class="subterminal-title">RISK NOTES</div>',
                    unsafe_allow_html=True,
                )

                st.warning(row.get("risk_note", "No risk note available."))
                st.write(f"Market diagnostic: `{row.get('market_diagnostic', 'N/A')}`")


# ============================================================
# TAB 5: MODEL NOTES
# ============================================================

with tabs[4]:
    st.markdown(
        '<div class="section-title">Model Notes</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">Pricing logic, execution assumptions and research interpretation.</div>',
        unsafe_allow_html=True,
    )

    m1, m2 = st.columns(2)

    with m1:
        st.markdown(
            """
            ### Core Pricing Logic

            Put-call parity:

            `C - P = S * exp(-qT) - K * exp(-rT)`

            Synthetic forward construction:

            `Buy synthetic forward = buy call at ask, sell put at bid`

            `Sell synthetic forward = sell call at bid, buy put at ask`

            The scanner compares theoretical parity with executable synthetic forward prices.
            """
        )

    with m2:
        st.markdown(
            """
            ### Research Framework

            The platform applies:

            - bid/ask execution assumptions
            - stock slippage assumptions
            - spread and liquidity filters
            - moneyness filters
            - data-quality checks
            - snapshot logging
            - signal decay analysis
            - signal persistence scoring
            - transition and half-life diagnostics
            """
        )

    st.divider()

    st.markdown(
        """
        ### Important Interpretation

        A flagged signal is not automatically tradable arbitrage.

        It is a research candidate requiring:

        - live quote validation
        - execution-cost verification
        - borrow and short-sale checks
        - dividend validation
        - latency and fill-risk analysis
        - professional-grade data before deployment
        """
    )
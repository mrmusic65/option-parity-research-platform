from pathlib import Path
from datetime import datetime
import pandas as pd


DATA_DIR = Path("data_logs")
DATA_DIR.mkdir(exist_ok=True)


def add_scan_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output["scan_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return output


def save_scan_snapshot(df: pd.DataFrame) -> Path:
    if df.empty:
        raise ValueError("Cannot save an empty scan result.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = DATA_DIR / f"scan_snapshot_{timestamp}.csv"

    df_with_timestamp = add_scan_timestamp(df)
    df_with_timestamp.to_csv(file_path, index=False)

    return file_path


def load_all_snapshots() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("scan_snapshot_*.csv"))

    if not files:
        return pd.DataFrame()

    frames = []

    for file in files:
        try:
            df = pd.read_csv(file)
            df["source_file"] = file.name
            frames.append(df)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)

    if "scan_timestamp" in combined.columns:
        combined["scan_timestamp"] = pd.to_datetime(
            combined["scan_timestamp"],
            errors="coerce"
        )

    return combined


def summarize_research_history(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_snapshots": 0,
            "total_rows": 0,
            "unique_tickers": 0,
            "research_candidates": 0,
            "watchlist": 0,
            "data_quality_issues": 0,
            "avg_edge": 0,
            "max_edge": 0,
        }

    return {
        "total_snapshots": df["source_file"].nunique() if "source_file" in df.columns else 0,
        "total_rows": len(df),
        "unique_tickers": df["ticker"].nunique() if "ticker" in df.columns else 0,
        "research_candidates": int((df["signal"] == "Research candidate").sum()) if "signal" in df.columns else 0,
        "watchlist": int((df["signal"] == "Watchlist").sum()) if "signal" in df.columns else 0,
        "data_quality_issues": int((df["signal"] == "Data quality issue").sum()) if "signal" in df.columns else 0,
        "avg_edge": round(df["executable_edge_after_costs"].mean(), 4)
        if "executable_edge_after_costs" in df.columns else 0,
        "max_edge": round(df["executable_edge_after_costs"].max(), 4)
        if "executable_edge_after_costs" in df.columns else 0,
    }


def signal_summary_by_ticker(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "ticker" not in df.columns or "signal" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby(["ticker", "signal"])
        .size()
        .reset_index(name="count")
        .pivot(index="ticker", columns="signal", values="count")
        .fillna(0)
        .reset_index()
    )


def edge_summary_by_ticker(df: pd.DataFrame) -> pd.DataFrame:
    required = {"ticker", "executable_edge_after_costs", "edge_to_spread", "liquidity_score"}

    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame()

    return (
        df.groupby("ticker")
        .agg(
            avg_edge=("executable_edge_after_costs", "mean"),
            max_edge=("executable_edge_after_costs", "max"),
            avg_edge_to_spread=("edge_to_spread", "mean"),
            avg_liquidity_score=("liquidity_score", "mean"),
            observations=("ticker", "count"),
        )
        .round(4)
        .reset_index()
        .sort_values("max_edge", ascending=False)
    )


def time_series_signal_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "scan_timestamp" not in df.columns or "signal" not in df.columns:
        return pd.DataFrame()

    temp = df.copy()
    temp["scan_date"] = temp["scan_timestamp"].dt.strftime("%Y-%m-%d %H:%M")

    return (
        temp.groupby(["scan_date", "signal"])
        .size()
        .reset_index(name="count")
        .pivot(index="scan_date", columns="signal", values="count")
        .fillna(0)
        .reset_index()
    )
def signal_decay_analysis(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "ticker",
        "expiry",
        "strike",
        "scan_timestamp",
        "executable_edge_after_costs",
        "signal",
    }

    if df.empty or not required_columns.issubset(df.columns):
        return pd.DataFrame()

    temp = df.copy()
    temp = temp.dropna(subset=["scan_timestamp", "executable_edge_after_costs"])

    temp = temp.sort_values(
        ["ticker", "expiry", "strike", "scan_timestamp"]
    )

    grouped_results = []

    for (ticker, expiry, strike), group in temp.groupby(["ticker", "expiry", "strike"]):
        if len(group) < 2:
            continue

        first_row = group.iloc[0]
        last_row = group.iloc[-1]

        first_edge = first_row["executable_edge_after_costs"]
        last_edge = last_row["executable_edge_after_costs"]

        edge_change = last_edge - first_edge
        edge_decay = first_edge - last_edge

        if first_edge != 0:
            decay_pct = edge_decay / abs(first_edge)
        else:
            decay_pct = None

        first_time = first_row["scan_timestamp"]
        last_time = last_row["scan_timestamp"]

        time_delta_hours = (
            (last_time - first_time).total_seconds() / 3600
            if pd.notna(first_time) and pd.notna(last_time)
            else None
        )

        grouped_results.append({
            "ticker": ticker,
            "expiry": expiry,
            "strike": strike,
            "observations": len(group),
            "first_timestamp": first_time,
            "last_timestamp": last_time,
            "time_delta_hours": round(time_delta_hours, 4) if time_delta_hours is not None else None,
            "first_edge": round(first_edge, 4),
            "last_edge": round(last_edge, 4),
            "edge_change": round(edge_change, 4),
            "edge_decay": round(edge_decay, 4),
            "decay_pct": round(decay_pct, 4) if decay_pct is not None else None,
            "first_signal": first_row["signal"],
            "last_signal": last_row["signal"],
        })

    if not grouped_results:
        return pd.DataFrame()

    output = pd.DataFrame(grouped_results)

    return output.sort_values(
        ["edge_decay", "observations"],
        ascending=[False, False]
    )
def signal_persistence_score(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "ticker",
        "expiry",
        "strike",
        "scan_timestamp",
        "source_file",
        "executable_edge_after_costs",
        "edge_to_spread",
        "liquidity_score",
        "signal",
    }

    if df.empty or not required_columns.issubset(df.columns):
        return pd.DataFrame()

    temp = df.copy()
    temp = temp.dropna(subset=["scan_timestamp", "executable_edge_after_costs"])

    total_snapshots = temp["source_file"].nunique()

    if total_snapshots == 0:
        return pd.DataFrame()

    results = []

    grouped = temp.groupby(["ticker", "expiry", "strike"])

    for (ticker, expiry, strike), group in grouped:
        observations = len(group)
        unique_snapshots = group["source_file"].nunique()

        avg_edge = group["executable_edge_after_costs"].mean()
        max_edge = group["executable_edge_after_costs"].max()
        min_edge = group["executable_edge_after_costs"].min()
        edge_std = group["executable_edge_after_costs"].std()

        avg_edge_to_spread = group["edge_to_spread"].mean()
        avg_liquidity = group["liquidity_score"].mean()

        positive_edge_rate = (
            (group["executable_edge_after_costs"] > 0).sum() / observations
        )

        research_rate = (
            (group["signal"] == "Research candidate").sum() / observations
        )

        watchlist_rate = (
            (group["signal"] == "Watchlist").sum() / observations
        )

        data_quality_issue_rate = (
            (group["signal"] == "Data quality issue").sum() / observations
        )

        recurrence_rate = unique_snapshots / total_snapshots

        if pd.isna(edge_std):
            edge_std = 0

        edge_stability = 1 - min(
            edge_std / (abs(avg_edge) + 1e-6),
            1
        )

        persistence_score = (
            recurrence_rate * 30
            + positive_edge_rate * 20
            + research_rate * 20
            + watchlist_rate * 10
            + edge_stability * 10
            + min(avg_liquidity / 100, 1) * 10
            - data_quality_issue_rate * 20
        )

        persistence_score = max(0, min(100, persistence_score))

        first_timestamp = group["scan_timestamp"].min()
        last_timestamp = group["scan_timestamp"].max()

        results.append({
            "ticker": ticker,
            "expiry": expiry,
            "strike": strike,
            "observations": observations,
            "unique_snapshots": unique_snapshots,
            "recurrence_rate": round(recurrence_rate, 4),
            "avg_edge": round(avg_edge, 4),
            "max_edge": round(max_edge, 4),
            "min_edge": round(min_edge, 4),
            "edge_std": round(edge_std, 4),
            "edge_stability": round(edge_stability, 4),
            "avg_edge_to_spread": round(avg_edge_to_spread, 4),
            "avg_liquidity_score": round(avg_liquidity, 4),
            "positive_edge_rate": round(positive_edge_rate, 4),
            "research_rate": round(research_rate, 4),
            "watchlist_rate": round(watchlist_rate, 4),
            "data_quality_issue_rate": round(data_quality_issue_rate, 4),
            "persistence_score": round(persistence_score, 2),
            "first_timestamp": first_timestamp,
            "last_timestamp": last_timestamp,
        })

    if not results:
        return pd.DataFrame()

    output = pd.DataFrame(results)

    return output.sort_values(
        ["persistence_score", "unique_snapshots", "avg_edge"],
        ascending=[False, False, False]
    )
def signal_quality_dashboard(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "highest_persistence": None,
            "best_avg_edge": None,
            "best_liquidity_adjusted": None,
            "most_unstable": None,
            "highest_data_quality_issue_rate": None,
            "most_recurring": None,
        }

    persistence_df = signal_persistence_score(df)

    if persistence_df.empty:
        return {
            "highest_persistence": None,
            "best_avg_edge": None,
            "best_liquidity_adjusted": None,
            "most_unstable": None,
            "highest_data_quality_issue_rate": None,
            "most_recurring": None,
        }

    temp = persistence_df.copy()

    temp["liquidity_adjusted_score"] = (
        temp["avg_edge"] * temp["avg_liquidity_score"]
    )

    highest_persistence = temp.sort_values(
        "persistence_score",
        ascending=False
    ).iloc[0]

    best_avg_edge = temp.sort_values(
        "avg_edge",
        ascending=False
    ).iloc[0]

    best_liquidity_adjusted = temp.sort_values(
        "liquidity_adjusted_score",
        ascending=False
    ).iloc[0]

    most_unstable = temp.sort_values(
        "edge_std",
        ascending=False
    ).iloc[0]

    highest_data_quality_issue_rate = temp.sort_values(
        "data_quality_issue_rate",
        ascending=False
    ).iloc[0]

    most_recurring = temp.sort_values(
        "recurrence_rate",
        ascending=False
    ).iloc[0]

    return {
        "highest_persistence": highest_persistence,
        "best_avg_edge": best_avg_edge,
        "best_liquidity_adjusted": best_liquidity_adjusted,
        "most_unstable": most_unstable,
        "highest_data_quality_issue_rate": highest_data_quality_issue_rate,
        "most_recurring": most_recurring,
    }
def signal_transition_matrix(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "ticker",
        "expiry",
        "strike",
        "scan_timestamp",
        "signal",
    }

    if df.empty or not required_columns.issubset(df.columns):
        return pd.DataFrame()

    temp = df.copy()
    temp = temp.dropna(subset=["scan_timestamp", "signal"])

    temp = temp.sort_values(
        ["ticker", "expiry", "strike", "scan_timestamp"]
    )

    transitions = []

    for (ticker, expiry, strike), group in temp.groupby(["ticker", "expiry", "strike"]):
        if len(group) < 2:
            continue

        group = group.sort_values("scan_timestamp")

        for i in range(len(group) - 1):
            current_row = group.iloc[i]
            next_row = group.iloc[i + 1]

            transitions.append({
                "ticker": ticker,
                "expiry": expiry,
                "strike": strike,
                "from_signal": current_row["signal"],
                "to_signal": next_row["signal"],
                "from_timestamp": current_row["scan_timestamp"],
                "to_timestamp": next_row["scan_timestamp"],
            })

    if not transitions:
        return pd.DataFrame()

    transition_df = pd.DataFrame(transitions)

    matrix = (
        transition_df
        .groupby(["from_signal", "to_signal"])
        .size()
        .reset_index(name="count")
        .pivot(index="from_signal", columns="to_signal", values="count")
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    return matrix


def edge_half_life_analysis(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "ticker",
        "expiry",
        "strike",
        "scan_timestamp",
        "executable_edge_after_costs",
    }

    if df.empty or not required_columns.issubset(df.columns):
        return pd.DataFrame()

    temp = df.copy()
    temp = temp.dropna(subset=["scan_timestamp", "executable_edge_after_costs"])

    temp = temp.sort_values(
        ["ticker", "expiry", "strike", "scan_timestamp"]
    )

    results = []

    for (ticker, expiry, strike), group in temp.groupby(["ticker", "expiry", "strike"]):
        if len(group) < 2:
            continue

        group = group.sort_values("scan_timestamp")

        first_row = group.iloc[0]
        first_edge = first_row["executable_edge_after_costs"]

        if first_edge <= 0:
            continue

        half_edge = first_edge / 2

        half_life_hours = None
        half_life_timestamp = None

        for _, row in group.iloc[1:].iterrows():
            current_edge = row["executable_edge_after_costs"]

            if current_edge <= half_edge:
                half_life_timestamp = row["scan_timestamp"]
                half_life_hours = (
                    (half_life_timestamp - first_row["scan_timestamp"])
                    .total_seconds()
                    / 3600
                )
                break

        last_row = group.iloc[-1]
        last_edge = last_row["executable_edge_after_costs"]

        total_time_hours = (
            (last_row["scan_timestamp"] - first_row["scan_timestamp"])
            .total_seconds()
            / 3600
        )

        edge_decay = first_edge - last_edge

        results.append({
            "ticker": ticker,
            "expiry": expiry,
            "strike": strike,
            "observations": len(group),
            "first_timestamp": first_row["scan_timestamp"],
            "last_timestamp": last_row["scan_timestamp"],
            "first_edge": round(first_edge, 4),
            "last_edge": round(last_edge, 4),
            "half_edge_threshold": round(half_edge, 4),
            "half_life_reached": half_life_hours is not None,
            "half_life_hours": round(half_life_hours, 4) if half_life_hours is not None else None,
            "total_time_hours": round(total_time_hours, 4),
            "edge_decay": round(edge_decay, 4),
        })

    if not results:
        return pd.DataFrame()

    output = pd.DataFrame(results)

    return output.sort_values(
        ["half_life_reached", "half_life_hours", "edge_decay"],
        ascending=[False, True, False]
    )
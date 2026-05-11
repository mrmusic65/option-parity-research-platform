import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Database,
  Gauge,
  LineChart,
  Loader2,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Zap,
} from "lucide-react";
import "./App.css";
import BlackScholesPanel from "./BlackScholesPanel";

const API_BASE_URL = "http://127.0.0.1:8000";

const defaultSummary = {
  tickers: 0,
  rows: 0,
  research: 0,
  watchlist: 0,
  data_issues: 0,
  no_trade: 0,
  max_edge: 0,
  avg_confidence: 0,
  avg_liquidity: 0,
};

const defaultFilters = {
  risk_free_rate: 0.05,
  dividend_yield: 0.005,
  stock_slippage_bps: 2.0,
  min_net_edge: 0.05,
  max_total_spread: 1.0,
  min_open_interest: 500,
  min_liquidity_score: 50,
  min_edge_to_spread: 0.5,
  min_total_spread_floor: 0.05,
  max_moneyness_deviation: 0.2,
  min_option_bid: 0.01,
};

function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "0";
  }

  return Number(value).toFixed(decimals);
}

function signalClass(signal) {
  if (!signal) return "";

  return signal
    .toLowerCase()
    .replaceAll(" ", "-")
    .replaceAll("_", "-");
}

function safeValue(value) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  return value;
}

function App() {
  const [tickersInput, setTickersInput] = useState("AAPL, MSFT");
  const [filters, setFilters] = useState(defaultFilters);

  const [scanData, setScanData] = useState({
    summary: defaultSummary,
    rows: [],
    errors: [],
  });

  const [researchData, setResearchData] = useState({
    summary: {},
    decay: [],
    persistence: [],
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isResearchLoading, setIsResearchLoading] = useState(false);
  const [lastScanStatus, setLastScanStatus] = useState("READY");
  const [selectedTrade, setSelectedTrade] = useState(null);

  const tickers = useMemo(() => {
    return tickersInput
      .split(",")
      .map((ticker) => ticker.trim().toUpperCase())
      .filter(Boolean);
  }, [tickersInput]);

const topSignals = useMemo(() => {
  return scanData.rows.slice(0, 12);
}, [scanData.rows]);

  const diagnosticRows = useMemo(() => {
    return scanData.rows.slice(0, 12);
  }, [scanData.rows]);

  function updateFilter(key, value) {
    setFilters((previous) => ({
      ...previous,
      [key]: value,
    }));
  }

  function resetFilters() {
    setFilters(defaultFilters);
  }

  async function runScan({ saveSnapshot = false } = {}) {
    alert("Run Scan clicked");

    setIsLoading(true);
    setLastScanStatus("RUNNING");
    setSelectedTrade(null);

    try {
      const response = await fetch(`${API_BASE_URL}/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tickers,
          scan_mode: "single",
          max_expiries_per_ticker: 1,
          risk_free_rate: Number(filters.risk_free_rate),
          dividend_yield: Number(filters.dividend_yield),
          stock_slippage_bps: Number(filters.stock_slippage_bps),
          min_net_edge: Number(filters.min_net_edge),
          max_total_spread: Number(filters.max_total_spread),
          min_open_interest: Number(filters.min_open_interest),
          min_liquidity_score: Number(filters.min_liquidity_score),
          min_edge_to_spread: Number(filters.min_edge_to_spread),
          min_total_spread_floor: Number(filters.min_total_spread_floor),
          max_moneyness_deviation: Number(filters.max_moneyness_deviation),
          min_option_bid: Number(filters.min_option_bid),
          save_snapshot: saveSnapshot,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      setScanData({
        summary: data.summary || defaultSummary,
        rows: data.rows || [],
        errors: data.errors || [],
      });

      const firstCandidate = (data.rows || []).find((row) =>
        ["Research candidate", "Watchlist"].includes(row.signal)
      );

      setSelectedTrade(firstCandidate || null);
      setLastScanStatus("ONLINE");

      if (saveSnapshot) {
        await loadResearchSummary();
      }
    } catch (error) {
      setLastScanStatus("ERROR");
      setScanData((previous) => ({
        ...previous,
        errors: [String(error.message || error)],
      }));
    } finally {
      setIsLoading(false);
    }
  }

  async function loadResearchSummary() {
    setIsResearchLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/research/summary`);

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      setResearchData({
        summary: data.summary || {},
        decay: data.decay || [],
        persistence: data.persistence || [],
      });
    } catch (error) {
      setScanData((previous) => ({
        ...previous,
        errors: [String(error.message || error)],
      }));
    } finally {
      setIsResearchLoading(false);
    }
  }

  const metrics = [
    {
      label: "Universe",
      value: String(scanData.summary.tickers || tickers.length),
      sub: "tickers scanned",
      icon: Search,
    },
    {
      label: "Rows",
      value: String(scanData.summary.rows || 0),
      sub: "option pairs",
      icon: Database,
    },
    {
      label: "Max Edge",
      value: formatNumber(scanData.summary.max_edge, 4),
      sub: "after costs",
      icon: Zap,
    },
    {
      label: "Confidence",
      value: formatNumber(scanData.summary.avg_confidence, 2),
      sub: "avg score",
      icon: Gauge,
    },
  ];

  return (
    <main className="terminal-shell">
      <section className="hero">
        <div>
          <p className="kicker">OPTIONS RELATIVE VALUE TERMINAL</p>
          <h1>Synthetic Forward & Parity Research Desk</h1>
          <p className="subtitle">
            Institutional dashboard for put-call parity diagnostics, synthetic
            forwards, execution-aware signal ranking, and longitudinal signal
            research.
          </p>

          <div className="pills">
            <span>LIVE CHAIN SCAN</span>
            <span>PARITY ENGINE</span>
            <span>EXECUTION FILTERS</span>
            <span>SIGNAL DECAY</span>
          </div>
        </div>

        <div className="status-panel">
          <div>
            <span>MODE</span>
            <strong>RESEARCH</strong>
          </div>
          <div>
            <span>DATA</span>
            <strong>YFINANCE</strong>
          </div>
          <div>
            <span>ENGINE</span>
            <strong>PARITY</strong>
          </div>
          <div>
            <span>STATUS</span>
            <strong className={lastScanStatus === "ERROR" ? "red" : "green"}>
              {lastScanStatus}
            </strong>
          </div>
        </div>
      </section>

      <section className="command-strip">
        &gt; LOAD UNIVERSE: {tickers.join(", ") || "NONE"} | ENGINE:
        PUT-CALL PARITY | MODE: EXECUTION-AWARE | STATUS: {lastScanStatus}
      </section>

      <section className="control-panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">SCAN COMMAND</p>
            <h2>Live Universe</h2>
          </div>
          <SlidersHorizontal size={22} />
        </div>

        <div className="input-row">
          <input
            value={tickersInput}
            onChange={(event) => setTickersInput(event.target.value)}
            placeholder="AAPL, MSFT, NVDA"
          />

          <button
            onClick={() => runScan()}
            disabled={isLoading || tickers.length === 0}
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="spin" />
                Running Scan
              </>
            ) : (
              "Run Scan"
            )}
          </button>
        </div>

        <div className="advanced-controls">
          <div className="control-title">
            <span>Research Controls</span>
            <button className="secondary-button" onClick={resetFilters}>
              Reset
            </button>
          </div>

          <div className="filter-grid">
            <label>
              Risk-free rate
              <input
                type="number"
                step="0.005"
                value={filters.risk_free_rate}
                onChange={(event) =>
                  updateFilter("risk_free_rate", event.target.value)
                }
              />
            </label>

            <label>
              Dividend yield
              <input
                type="number"
                step="0.001"
                value={filters.dividend_yield}
                onChange={(event) =>
                  updateFilter("dividend_yield", event.target.value)
                }
              />
            </label>

            <label>
              Stock slippage bps
              <input
                type="number"
                step="0.5"
                value={filters.stock_slippage_bps}
                onChange={(event) =>
                  updateFilter("stock_slippage_bps", event.target.value)
                }
              />
            </label>

            <label>
              Min net edge
              <input
                type="number"
                step="0.01"
                value={filters.min_net_edge}
                onChange={(event) =>
                  updateFilter("min_net_edge", event.target.value)
                }
              />
            </label>

            <label>
              Max total spread
              <input
                type="number"
                step="0.1"
                value={filters.max_total_spread}
                onChange={(event) =>
                  updateFilter("max_total_spread", event.target.value)
                }
              />
            </label>

            <label>
              Min open interest
              <input
                type="number"
                step="100"
                value={filters.min_open_interest}
                onChange={(event) =>
                  updateFilter("min_open_interest", event.target.value)
                }
              />
            </label>

            <label>
              Min liquidity score
              <input
                type="number"
                step="5"
                value={filters.min_liquidity_score}
                onChange={(event) =>
                  updateFilter("min_liquidity_score", event.target.value)
                }
              />
            </label>

            <label>
              Min edge/spread
              <input
                type="number"
                step="0.1"
                value={filters.min_edge_to_spread}
                onChange={(event) =>
                  updateFilter("min_edge_to_spread", event.target.value)
                }
              />
            </label>

            <label>
              Max moneyness deviation
              <input
                type="number"
                step="0.05"
                value={filters.max_moneyness_deviation}
                onChange={(event) =>
                  updateFilter("max_moneyness_deviation", event.target.value)
                }
              />
            </label>
          </div>
        </div>

        {scanData.errors.length > 0 && (
          <div className="error-box">
            <AlertTriangle size={16} />
            <div>
              {scanData.errors.map((error, index) => (
                <p key={`${error}-${index}`}>{error}</p>
              ))}
            </div>
          </div>
        )}
      </section>
<div className="empty-state small">
  DEBUG: rows loaded = {scanData.rows.length}
</div>
      <section className="grid metrics-grid">
        {metrics.map((item) => {
          const Icon = item.icon;

          return (
            <div className="metric-card" key={item.label}>
              <div className="metric-top">
                <span>{item.label}</span>
                <Icon size={18} />
              </div>
              <strong>{item.value}</strong>
              <p>{item.sub}</p>
            </div>
          );
        })}
      </section>

      <section className="grid main-grid">
        <div className="panel wide">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">SIGNAL MATRIX</p>
              <h2>Top Research Signals</h2>
            </div>
            <button
              onClick={() => runScan()}
              disabled={isLoading || tickers.length === 0}
            >
              {isLoading ? "Scanning..." : "Refresh"}
            </button>
          </div>

          {topSignals.length === 0 ? (
            <div className="empty-state">
              Run a scan to populate option-chain diagnostics.
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Expiry</th>
                  <th>Strike</th>
                  <th>Signal</th>
                  <th>Best Trade</th>
                  <th>Net Edge</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {topSignals.map((row, index) => {
                  const isSelected =
                    selectedTrade &&
                    selectedTrade.ticker === row.ticker &&
                    selectedTrade.expiry === row.expiry &&
                    selectedTrade.strike === row.strike;

                  return (
                    <tr
                      key={`${row.ticker}-${row.expiry}-${row.strike}-${index}`}
                      onClick={() => setSelectedTrade(row)}
                      className={isSelected ? "selected-row" : "clickable-row"}
                    >
                      <td>{row.ticker}</td>
                      <td>{row.expiry}</td>
                      <td>{row.strike}</td>
                      <td>
                        <span className={`badge ${signalClass(row.signal)}`}>
                          {row.signal}
                        </span>
                      </td>
                      <td>{row.best_trade}</td>
                      <td>{formatNumber(row.executable_edge_after_costs, 4)}</td>
                      <td>{formatNumber(row.confidence_score, 2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="panel">
          <p className="panel-kicker">RESEARCH STATE</p>
          <h2>Signal Quality</h2>

          <div className="quality-stack">
            <div>
              <span>Research</span>
              <strong>{scanData.summary.research || 0}</strong>
            </div>
            <div>
              <span>Watchlist</span>
              <strong>{scanData.summary.watchlist || 0}</strong>
            </div>
            <div>
              <span>Data Issues</span>
              <strong>{scanData.summary.data_issues || 0}</strong>
            </div>
            <div>
              <span>Avg Liquidity</span>
              <strong>{formatNumber(scanData.summary.avg_liquidity, 2)}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="panel trade-diagnostics-panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">TRADE DIAGNOSTICS</p>
            <h2>Selected Synthetic Forward Candidate</h2>
          </div>

          <button
            onClick={() => runScan({ saveSnapshot: true })}
            disabled={isLoading || tickers.length === 0}
          >
            Save Snapshot
          </button>
        </div>

        {!selectedTrade ? (
          <div className="empty-state">
            Select a signal from the table above to inspect full parity,
            execution and risk diagnostics.
          </div>
        ) : (
          <div className="trade-grid">
            <div className="trade-card">
              <p className="panel-kicker">CONTRACT</p>
              <div className="detail-row">
                <span>Ticker</span>
                <strong>{safeValue(selectedTrade.ticker)}</strong>
              </div>
              <div className="detail-row">
                <span>Expiry</span>
                <strong>{safeValue(selectedTrade.expiry)}</strong>
              </div>
              <div className="detail-row">
                <span>Strike</span>
                <strong>{safeValue(selectedTrade.strike)}</strong>
              </div>
              <div className="detail-row">
                <span>Spot</span>
                <strong>{formatNumber(selectedTrade.spot, 2)}</strong>
              </div>
              <div className="detail-row">
                <span>Moneyness</span>
                <strong>{formatNumber(selectedTrade.moneyness, 4)}</strong>
              </div>
            </div>

            <div className="trade-card">
              <p className="panel-kicker">EXECUTION</p>
              <div className="detail-row">
                <span>Best Trade</span>
                <strong>{safeValue(selectedTrade.best_trade)}</strong>
              </div>
              <div className="detail-row">
                <span>Net Edge</span>
                <strong className="green">
                  {formatNumber(selectedTrade.executable_edge_after_costs, 4)}
                </strong>
              </div>
              <div className="detail-row">
                <span>Edge / Spread</span>
                <strong>{formatNumber(selectedTrade.edge_to_spread, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Stock Slippage</span>
                <strong>{formatNumber(selectedTrade.stock_slippage_cost, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Signal</span>
                <strong>{safeValue(selectedTrade.signal)}</strong>
              </div>
            </div>

            <div className="trade-card">
              <p className="panel-kicker">OPTION MARKET</p>
              <div className="detail-row">
                <span>Call Bid / Ask</span>
                <strong>
                  {safeValue(selectedTrade.call_bid)} / {safeValue(selectedTrade.call_ask)}
                </strong>
              </div>
              <div className="detail-row">
                <span>Put Bid / Ask</span>
                <strong>
                  {safeValue(selectedTrade.put_bid)} / {safeValue(selectedTrade.put_ask)}
                </strong>
              </div>
              <div className="detail-row">
                <span>Total Spread</span>
                <strong>{formatNumber(selectedTrade.total_spread, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Total OI</span>
                <strong>{safeValue(selectedTrade.total_oi)}</strong>
              </div>
              <div className="detail-row">
                <span>Liquidity Score</span>
                <strong>{formatNumber(selectedTrade.liquidity_score, 2)}</strong>
              </div>
            </div>

            <div className="trade-card">
              <p className="panel-kicker">PARITY BREAKDOWN</p>
              <div className="detail-row">
                <span>Theoretical Parity</span>
                <strong>{formatNumber(selectedTrade.theoretical_parity, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Mid Market Parity</span>
                <strong>{formatNumber(selectedTrade.mid_market_parity, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Mid Mispricing</span>
                <strong>{formatNumber(selectedTrade.mid_mispricing, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>PV Strike</span>
                <strong>{formatNumber(selectedTrade.pv_strike, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Dividend Adj. Spot</span>
                <strong>{formatNumber(selectedTrade.dividend_adjusted_spot, 4)}</strong>
              </div>
            </div>

            <div className="trade-card">
              <p className="panel-kicker">IMPLIED MARKET</p>
              <div className="detail-row">
                <span>Input Rate</span>
                <strong>{formatNumber(selectedTrade.risk_free_rate, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Implied Rate</span>
                <strong>{formatNumber(selectedTrade.implied_rate_mid, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Input Dividend</span>
                <strong>{formatNumber(selectedTrade.dividend_yield, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Implied Dividend</span>
                <strong>{formatNumber(selectedTrade.implied_dividend_yield_mid, 4)}</strong>
              </div>
              <div className="detail-row">
                <span>Confidence</span>
                <strong>{formatNumber(selectedTrade.confidence_score, 2)}</strong>
              </div>
            </div>

            <div className="trade-card risk-card">
              <p className="panel-kicker">RISK NOTES</p>
              <p>{safeValue(selectedTrade.risk_note)}</p>
              <p className="diagnostic-note">
                {safeValue(selectedTrade.market_diagnostic)}
              </p>
            </div>
          </div>
        )}
      </section>

      <section className="panel research-lab-panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">RESEARCH LAB</p>
            <h2>Historical Signal Research</h2>
          </div>

          <button onClick={loadResearchSummary} disabled={isResearchLoading}>
            {isResearchLoading ? (
              <>
                <Loader2 size={18} className="spin" />
                Loading Research
              </>
            ) : (
              "Load Research Lab"
            )}
          </button>
        </div>

        {!researchData.summary || Object.keys(researchData.summary).length === 0 ? (
          <div className="empty-state">
            Save at least one snapshot, then load Research Lab to inspect signal
            persistence, decay and historical scanner behavior.
          </div>
        ) : (
          <>
            <div className="research-metrics">
              <div>
                <span>Snapshots</span>
                <strong>{researchData.summary.total_snapshots || 0}</strong>
              </div>
              <div>
                <span>Historical Rows</span>
                <strong>{researchData.summary.total_rows || 0}</strong>
              </div>
              <div>
                <span>Unique Tickers</span>
                <strong>{researchData.summary.unique_tickers || 0}</strong>
              </div>
              <div>
                <span>Research Candidates</span>
                <strong>{researchData.summary.research_candidates || 0}</strong>
              </div>
              <div>
                <span>Watchlist</span>
                <strong>{researchData.summary.watchlist || 0}</strong>
              </div>
              <div>
                <span>Data Issues</span>
                <strong>{researchData.summary.data_quality_issues || 0}</strong>
              </div>
            </div>

            <div className="research-grid">
              <div className="research-card">
                <p className="panel-kicker">PERSISTENCE ENGINE</p>
                <h3>Top Persistent Signals</h3>

                {researchData.persistence.length === 0 ? (
                  <div className="empty-state small">
                    No persistence data available yet.
                  </div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Strike</th>
                        <th>Snapshots</th>
                        <th>Avg Edge</th>
                        <th>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {researchData.persistence.slice(0, 8).map((row, index) => (
                        <tr key={`persistence-${index}`}>
                          <td>{row.ticker}</td>
                          <td>{row.strike}</td>
                          <td>{row.unique_snapshots}</td>
                          <td>{formatNumber(row.avg_edge, 4)}</td>
                          <td>{formatNumber(row.persistence_score, 2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="research-card">
                <p className="panel-kicker">SIGNAL DECAY</p>
                <h3>Top Edge Decay</h3>

                {researchData.decay.length === 0 ? (
                  <div className="empty-state small">
                    No signal decay data available yet.
                  </div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Strike</th>
                        <th>Obs</th>
                        <th>First Edge</th>
                        <th>Last Edge</th>
                        <th>Decay</th>
                      </tr>
                    </thead>
                    <tbody>
                      {researchData.decay.slice(0, 8).map((row, index) => (
                        <tr key={`decay-${index}`}>
                          <td>{row.ticker}</td>
                          <td>{row.strike}</td>
                          <td>{row.observations}</td>
                          <td>{formatNumber(row.first_edge, 4)}</td>
                          <td>{formatNumber(row.last_edge, 4)}</td>
                          <td>{formatNumber(row.edge_decay, 4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </>
        )}
      </section>
<BlackScholesPanel />
      <section className="grid lower-grid">
        <div className="panel">
          <p className="panel-kicker">MARKET DIAGNOSTICS</p>
          <h2>Implied Financing</h2>

          {diagnosticRows.length === 0 ? (
            <div className="empty-state small">No diagnostics loaded yet.</div>
          ) : (
            <div className="mini-table">
              {diagnosticRows.slice(0, 6).map((row, index) => (
                <div key={`${row.ticker}-diag-${index}`}>
                  <span>
                    {row.ticker} K={row.strike}
                  </span>
                  <strong>
                    {row.implied_rate_mid === null
                      ? "N/A"
                      : formatNumber(row.implied_rate_mid, 4)}
                  </strong>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <p className="panel-kicker">EXECUTION</p>
          <h2>Risk Controls</h2>
          <ul className="risk-list">
            <li>
              <ShieldCheck size={16} /> Bid/ask-aware synthetic forward pricing
            </li>
            <li>
              <ShieldCheck size={16} /> Moneyness and spread filters
            </li>
            <li>
              <ShieldCheck size={16} /> Open interest and liquidity scoring
            </li>
            <li>
              <ShieldCheck size={16} /> Snapshot logging for signal validation
            </li>
          </ul>
        </div>

        <div className="panel">
          <p className="panel-kicker">LIVE MONITOR</p>
          <h2>Engine Status</h2>
          <div className="monitor">
            <Activity size={18} />
            <span>Backend API: {lastScanStatus}</span>
          </div>
          <div className="monitor">
            <LineChart size={18} />
            <span>Rows loaded: {scanData.summary.rows || 0}</span>
          </div>
          <div className="monitor">
            <Database size={18} />
            <span>Scanner endpoint: /scan</span>
          </div>
        </div>
      </section>
    </main>
  );
}

export default App;
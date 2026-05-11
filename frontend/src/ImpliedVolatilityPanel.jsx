import { useState } from "react";
import { Loader2, TrendingUp } from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000";

const defaultInputs = {
  option_type: "call",
  market_price: 10.450584,
  spot: 100,
  strike: 100,
  time_to_expiry: 1,
  risk_free_rate: 0.05,
  dividend_yield: 0,
  min_vol: 0.0001,
  max_vol: 5,
  tolerance: 0.000001,
  max_iterations: 100,
};

function formatNumber(value, decimals = 6) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }

  return Number(value).toFixed(decimals);
}

function ImpliedVolatilityPanel() {
  const [inputs, setInputs] = useState(defaultInputs);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  function updateInput(key, value) {
    setInputs((previous) => ({
      ...previous,
      [key]: value,
    }));
  }

  function resetInputs() {
    setInputs(defaultInputs);
    setResult(null);
    setErrorMessage("");
  }

  async function calculateImpliedVolatility() {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/implied-volatility`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          option_type: inputs.option_type,
          market_price: Number(inputs.market_price),
          spot: Number(inputs.spot),
          strike: Number(inputs.strike),
          time_to_expiry: Number(inputs.time_to_expiry),
          risk_free_rate: Number(inputs.risk_free_rate),
          dividend_yield: Number(inputs.dividend_yield),
          min_vol: Number(inputs.min_vol),
          max_vol: Number(inputs.max_vol),
          tolerance: Number(inputs.tolerance),
          max_iterations: Number(inputs.max_iterations),
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setErrorMessage(String(error.message || error));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="panel implied-vol-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">IMPLIED VOLATILITY LAB</p>
          <h2>Market Price → Implied Volatility</h2>
        </div>

        <TrendingUp size={22} />
      </div>

      <p className="iv-description">
        Estimate the volatility implied by an observed option market price.
        This is the inverse of Black-Scholes pricing and is a core building
        block for volatility surfaces, smile/skew diagnostics, and options
        relative-value research.
      </p>

      <div className="iv-grid">
        <div className="iv-input-card">
          <div className="iv-form-grid">
            <label>
              Option Type
              <select
                value={inputs.option_type}
                onChange={(event) =>
                  updateInput("option_type", event.target.value)
                }
              >
                <option value="call">Call</option>
                <option value="put">Put</option>
              </select>
            </label>

            <label>
              Market Price
              <input
                type="number"
                step="0.01"
                value={inputs.market_price}
                onChange={(event) =>
                  updateInput("market_price", event.target.value)
                }
              />
            </label>

            <label>
              Spot
              <input
                type="number"
                step="1"
                value={inputs.spot}
                onChange={(event) => updateInput("spot", event.target.value)}
              />
            </label>

            <label>
              Strike
              <input
                type="number"
                step="1"
                value={inputs.strike}
                onChange={(event) => updateInput("strike", event.target.value)}
              />
            </label>

            <label>
              Time to Expiry
              <input
                type="number"
                step="0.01"
                value={inputs.time_to_expiry}
                onChange={(event) =>
                  updateInput("time_to_expiry", event.target.value)
                }
              />
            </label>

            <label>
              Risk-Free Rate
              <input
                type="number"
                step="0.005"
                value={inputs.risk_free_rate}
                onChange={(event) =>
                  updateInput("risk_free_rate", event.target.value)
                }
              />
            </label>

            <label>
              Dividend Yield
              <input
                type="number"
                step="0.001"
                value={inputs.dividend_yield}
                onChange={(event) =>
                  updateInput("dividend_yield", event.target.value)
                }
              />
            </label>

            <label>
              Max Vol Bound
              <input
                type="number"
                step="0.5"
                value={inputs.max_vol}
                onChange={(event) => updateInput("max_vol", event.target.value)}
              />
            </label>
          </div>

          <div className="iv-actions">
            <button onClick={calculateImpliedVolatility} disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 size={18} className="spin" />
                  Solving IV
                </>
              ) : (
                "Solve Implied Volatility"
              )}
            </button>

            <button className="secondary-button" onClick={resetInputs}>
              Reset
            </button>
          </div>

          {errorMessage && <div className="iv-error">{errorMessage}</div>}
        </div>

        <div className="iv-result-card">
          {!result ? (
            <div className="empty-state small">
              Run the solver to display implied volatility, model price,
              pricing error and convergence diagnostics.
            </div>
          ) : (
            <>
              <div className="iv-main-result">
                <span>Implied Volatility</span>
                <strong>
                  {result.implied_volatility === null
                    ? "N/A"
                    : `${formatNumber(result.implied_volatility * 100, 2)}%`}
                </strong>
              </div>

              <div className="iv-result-grid">
                <div>
                  <span>Converged</span>
                  <strong className={result.converged ? "green" : "red"}>
                    {result.converged ? "YES" : "NO"}
                  </strong>
                </div>

                <div>
                  <span>Model Price</span>
                  <strong>{formatNumber(result.model_price, 6)}</strong>
                </div>

                <div>
                  <span>Market Price</span>
                  <strong>{formatNumber(result.market_price, 6)}</strong>
                </div>

                <div>
                  <span>Pricing Error</span>
                  <strong>{formatNumber(result.pricing_error, 8)}</strong>
                </div>

                <div>
                  <span>Iterations</span>
                  <strong>{result.iterations}</strong>
                </div>

                <div>
                  <span>Message</span>
                  <strong>{result.message}</strong>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

export default ImpliedVolatilityPanel;
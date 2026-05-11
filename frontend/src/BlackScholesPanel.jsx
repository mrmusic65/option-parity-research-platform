import { useState } from "react";
import { Calculator, Loader2 } from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000";

const defaultInputs = {
  option_type: "call",
  spot: 100,
  strike: 100,
  time_to_expiry: 1,
  risk_free_rate: 0.05,
  dividend_yield: 0,
  volatility: 0.2,
};

function formatNumber(value, decimals = 6) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "0";
  }

  return Number(value).toFixed(decimals);
}

function BlackScholesPanel() {
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

  async function calculateBlackScholes() {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/black-scholes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          option_type: inputs.option_type,
          spot: Number(inputs.spot),
          strike: Number(inputs.strike),
          time_to_expiry: Number(inputs.time_to_expiry),
          risk_free_rate: Number(inputs.risk_free_rate),
          dividend_yield: Number(inputs.dividend_yield),
          volatility: Number(inputs.volatility),
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

  function resetInputs() {
    setInputs(defaultInputs);
    setResult(null);
    setErrorMessage("");
  }

  return (
    <section className="panel black-scholes-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">BLACK-SCHOLES LAB</p>
          <h2>Pricing & Greeks</h2>
        </div>

        <Calculator size={22} />
      </div>

      <p className="bs-description">
        Calculate theoretical option value and Greeks using the Black-Scholes
        framework. This module complements the parity scanner by adding
        volatility-sensitive option diagnostics.
      </p>

      <div className="bs-grid">
        <div className="bs-input-card">
          <div className="bs-form-grid">
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
              Volatility
              <input
                type="number"
                step="0.01"
                value={inputs.volatility}
                onChange={(event) =>
                  updateInput("volatility", event.target.value)
                }
              />
            </label>
          </div>

          <div className="bs-actions">
            <button onClick={calculateBlackScholes} disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 size={18} className="spin" />
                  Calculating
                </>
              ) : (
                "Calculate"
              )}
            </button>

            <button className="secondary-button" onClick={resetInputs}>
              Reset
            </button>
          </div>

          {errorMessage && <div className="bs-error">{errorMessage}</div>}
        </div>

        <div className="bs-result-card">
          {!result ? (
            <div className="empty-state small">
              Run a calculation to display price, Greeks, d1 and d2.
            </div>
          ) : (
            <>
              <div className="bs-price-box">
                <span>Theoretical Price</span>
                <strong>{formatNumber(result.price, 4)}</strong>
              </div>

              <div className="greeks-grid">
                <div>
                  <span>Delta</span>
                  <strong>{formatNumber(result.delta, 6)}</strong>
                </div>
                <div>
                  <span>Gamma</span>
                  <strong>{formatNumber(result.gamma, 6)}</strong>
                </div>
                <div>
                  <span>Vega</span>
                  <strong>{formatNumber(result.vega, 6)}</strong>
                </div>
                <div>
                  <span>Theta</span>
                  <strong>{formatNumber(result.theta, 6)}</strong>
                </div>
                <div>
                  <span>Rho</span>
                  <strong>{formatNumber(result.rho, 6)}</strong>
                </div>
                <div>
                  <span>d1</span>
                  <strong>{formatNumber(result.d1, 6)}</strong>
                </div>
                <div>
                  <span>d2</span>
                  <strong>{formatNumber(result.d2, 6)}</strong>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

export default BlackScholesPanel;
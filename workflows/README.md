# Workflows

Calculations built on the data sources. Each workflow is a folder with a `README.md` (what it computes, the formula with a citation, which data source feeds it) and runnable code.

```
financial-analysis/
  income-statement/   margins, growth, operating leverage, quality of earnings
  balance-sheet/      liquidity, leverage, working capital, asset turnover
  cash-flow/          free cash flow, conversion, capex intensity, DCF inputs
options/
  volume/             volume and open interest analysis, put/call ratios
  volatility/         realised vs implied, term structure, skew, surfaces
  gamma/              gamma exposure, dealer positioning, flip levels
  greeks/             delta, vega, theta, rho, higher-order Greeks
```

Copy `_TEMPLATE.md` into a new folder under the right group to start one.

## Built so far

| Workflow | Computes | Data sources | Run offline |
| --- | --- | --- | --- |
| [financial-analysis/income-statement](financial-analysis/income-statement/README.md) | Margins, growth and operating leverage, point-in-time | SEC EDGAR | `python main.py --sample` |
| [options/greeks](options/greeks/README.md) | Implied volatility and BSM Greeks, checked against Cboe | Cboe delayed quotes, US Treasury yield curve | `python main.py --sample` |
| [options/gamma](options/gamma/README.md) | Dealer gamma exposure by strike, walls, gamma flip and a range-and-median sensitivity report | Cboe delayed quotes, SqueezeMetrics (reference) | `python main.py --sample` |
| [financial-analysis/balance-sheet](financial-analysis/balance-sheet/README.md) | Liquidity, leverage and working capital, point-in-time, with warnings for missing line items | SEC EDGAR | `python main.py --sample` |
| [financial-analysis/cash-flow](financial-analysis/cash-flow/README.md) | Free cash flow, conversion, capex intensity and shareholder payouts | SEC EDGAR | `python main.py --sample` |
| [financial-analysis/ratios](financial-analysis/ratios/README.md) | 41 ratios in 8 categories, by year or across peers; valuation at the filing-date price | SEC EDGAR, yfinance (valuation only) | `python main.py --sample` |
| [options/volatility](options/volatility/README.md) | Term structure, skew, realized vs implied, and a VIX replication check | Cboe delayed quotes, US Treasury yield curve, yfinance (realized only) | `python main.py --sample` |
| [options/volume](options/volume/README.md) | Put/call ratios, unusual activity, OI concentration, and OI change from a daily snapshot archive | Cboe delayed quotes | `python main.py --sample` |

Every workflow runs on live data by default (no API keys needed; SEC EDGAR needs `SEC_USER_AGENT`) and has a `--sample` mode that runs offline from its `sample/` folder.

The calculations themselves live in the shared library [`quanttk/`](../quanttk/README.md); each `main.py` loads data, calls the library and prints the report. Run `pytest` from the repo root to test both.

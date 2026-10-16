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
| [options/gamma](options/gamma/README.md) | Dealer gamma exposure by strike, walls and gamma flip | Cboe delayed quotes, SqueezeMetrics (reference) | `python main.py --sample` |

Every workflow runs on live data by default (no API keys needed; SEC EDGAR needs `SEC_USER_AGENT`) and has a `--sample` mode that runs offline from its `sample/` folder.

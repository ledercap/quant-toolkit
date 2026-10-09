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

# quanttk: the shared calculation library

The workflows in [`workflows/`](../workflows/README.md) are thin scripts on top of this package. Each calculation is written once here and reused, rather than copied between workflows. CLAUDE.md rule 5 allows a shared module once two or more workflows share code: the Greeks and gamma workflows already shared the Cboe loader and Black-Scholes code, and the three statement workflows share the EDGAR code.

Formulas and their citations stay in each workflow's README, next to the code that uses them (CLAUDE.md rule 4). The docstrings here name the same sources.

## Modules

| Module | What it does | Used by |
| --- | --- | --- |
| `quanttk.sources.edgar` | Ticker → CIK, every XBRL fact for a set of tags | income statement, balance sheet, cash flow, ratios |
| `quanttk.sources.cboe` | Delayed option chains and quotes; OCC symbol parsing; AM/PM settlement and time to expiry | greeks, gamma, volatility, volume |
| `quanttk.sources.treasury` | Par yield curve; continuous-rate conversion | greeks, volatility |
| `quanttk.sources.prices` | Daily closes (yfinance today; one function to swap for a licensed source) | ratios (valuation), volatility (realized) |
| `quanttk.sources.snapshots` | Parquet archive of option-chain snapshots, so history builds up | volume (open-interest change) |
| `quanttk.statements.concepts` | Line items → XBRL tags, in priority order (income statement, balance sheet, cash flow) | all statement workflows |
| `quanttk.statements.build` | Point-in-time annual selection (period amounts and year-end balances), growth, average balances | all statement workflows |
| `quanttk.statements.derived` | Derived items (total debt, net debt, EBITDA, free cash flow...) and the combined annual table | balance sheet, cash flow, ratios |
| `quanttk.ratios` | The ratio registry: every ratio defined once with category, formula and source | ratios |
| `quanttk.pricing.black_scholes` | BSM and Black-76 prices, implied volatility, Greeks | greeks, gamma, volatility |
| `quanttk.pricing.forwards` | Put-call-parity forward (Cboe VIX method) | greeks, volatility |
| `quanttk.options.surface` | Price a whole chain: rates, forwards, IV and Greeks per contract | greeks, volatility |
| `quanttk.options.gex` | Gamma exposure, flip profile, sensitivity range | gamma |
| `quanttk.options.volatility` | Term structure, smile and skew, realized volatility, VIX replication | volatility |
| `quanttk.options.volume` | Put/call ratios, unusual activity, open-interest concentration and change | volume |

## Install and test

The workflows run from a plain checkout without installing anything: each `main.py` adds the repo root to its import path when `quanttk` isn't installed. To install it as a package and run the tests:

```bash
pip install -e ".[all]"
pytest
```

`pytest` runs:
- **Unit tests:** published textbook values (Hull's Black-Scholes example), model identities (put-call parity, DuPont), finite-difference checks of every Greek, point-in-time selection, and the VIX formula on a synthetic flat-volatility chain.
- **Golden tests:** each workflow's offline `--sample` run must reproduce the output it produced before the refactor.

## Adding to it

- **Before writing code,** check whether a workflow needs something already here.
- **Keep functions pure where possible:** DataFrames in, DataFrames or Series out, no printing.
- **Every public function gets a docstring** naming its formula's source.
- **Add a test** for any new calculation, against a published value or an identity where one exists.

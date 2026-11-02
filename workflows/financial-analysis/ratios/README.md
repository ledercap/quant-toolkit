# Financial ratios: the ratio layer on top of the statements

**Computes:** every ratio in the `quanttk.ratios` registry (41 ratios in 8 categories), for one company by fiscal year or for several companies side by side. All are point-in-time as of any date:

| Category | Ratios |
| --- | --- |
| Profitability | gross, operating, EBITDA and net margin; ROA; ROE; ROIC |
| DuPont | net margin × asset turnover × equity multiplier (= ROE) |
| Liquidity | current, quick and cash ratios |
| Leverage | debt-to-equity, debt-to-assets, liabilities-to-assets, equity multiplier, net debt / EBITDA, interest coverage |
| Efficiency | asset turnover, DSO, DIO, DPO, cash conversion cycle |
| Cash quality | FCF margin, FCF conversion, accruals ratio, capex intensity, capex / depreciation, payout and total payout ratios |
| Growth | revenue, operating income, EPS and FCF growth |
| Valuation (with `--prices`) | P/E, P/B, EV/sales, EV/EBITDA, earnings yield, FCF yield |

Run `python main.py --list` to print every ratio with its formula and source.

**Inputs:**
- Income statement, balance sheet and cash flow line items from [`data-sources/sec-edgar.md`](../../../data-sources/sec-edgar.md), built by `quanttk.statements` (the same builder the income-statement, balance-sheet and cash-flow workflows use).
- With `--prices`: as-traded daily closes from [`data-sources/yfinance.md`](../../../data-sources/yfinance.md).

**Output:** a table of ratios (rows, grouped by category) by fiscal year or by company (columns), printed and written to `output/ratios_<TICKER>.csv` or `output/ratios_peers_<TICKERS>.csv`.

## Formula

Each ratio's formula is defined once in `quanttk/ratios/registry.py`, and `--list` prints them. The conventions that apply to all of them:

- **Average balances.** Ratios that divide a full-year amount by a balance use the average of the opening and closing balance: avg(X)<sub>t</sub> = (X<sub>t−1</sub> + X<sub>t</sub>) / 2. That covers ROA, ROE, ROIC, asset turnover, DSO, DIO and DPO. They need the prior fiscal year, so they're blank for a company's first reported year. (CFA Institute.)
- **DuPont.** ROE = (NI / Revenue) × (Revenue / avg Assets) × (avg Assets / avg Equity). With average balances the identity is exact, and the workflow prints the residual as a check. (CFA Institute.)
- **ROIC** = NOPAT / avg invested capital, where:
  - NOPAT = operating income × (1 − tax rate)
  - tax rate = income tax / pretax income, or 21% when that's outside 0–50%
  - invested capital = total debt + equity − cash and short-term investments (the financing view)

  (Koller, Goedhart and Wessels.)
- **Days ratios:** DSO = avg receivables / revenue × 365; DIO = avg inventory / cost of revenue × 365; DPO = avg payables / cost of revenue × 365; cash conversion cycle = DSO + DIO − DPO. (CFA Institute.)
- **Accruals ratio** = (net income − operating cash flow) / avg total assets. High values mean earnings are running ahead of cash. (Hribar and Collins 2002; Sloan 1996.)
- **Growth** = X<sub>t</sub> / X<sub>t−1</sub> − 1, between consecutive fiscal years only. For items that can be negative (operating income, EPS, FCF) it's blank when the prior year is ≤ 0.
- **Valuation:**
  - price = as-traded close on or before the date the year's first 10-K was filed
  - market cap = price × shares outstanding at fiscal year end
  - enterprise value = market cap + total debt − cash and short-term investments
  - P/E = price / diluted EPS; P/B = market cap / equity; EV/sales and EV/EBITDA as named; earnings yield = net income / market cap; FCF yield = FCF / market cap

  (Damodaran.)

Sources:
- **CFA:** CFA Institute, *International Financial Statement Analysis*, 4th ed. (2020), "Financial Analysis Techniques".
- **KGW:** Koller, Goedhart and Wessels, *Valuation: Measuring and Managing the Value of Companies*, 7th ed. (2020), McKinsey & Company.
- **HC:** Hribar, P. and Collins, D. (2002), "Errors in Estimating Accruals: Implications for Empirical Research", *Journal of Accounting Research* 40(1), 105–134; Sloan, R. (1996), "Do Stock Prices Fully Reflect Information in Accruals and Cash Flows about Future Earnings?", *The Accounting Review* 71(3), 289–315.
- **DAM:** Damodaran, A., *Investment Valuation*, 3rd ed. (2012), Wiley.

## Caveats

- **Valuation ratios use the price on the filing date.** That's when a backtest could first have seen the numbers. They are not today's multiples. The 10-K may be filed after the close on that date, so the price can be one day early. Earnings are usually announced (8-K) days before the 10-K anyway.
- **Personal-use prices.** `--prices` uses yfinance, which is personal-use only. For anything commercial, swap `quanttk.sources.prices.daily_closes` for a licensed source such as Massive. It's the only function to change.
- **Multiple share classes.** Market cap uses `CommonStockSharesOutstanding`. For companies with several share classes (Alphabet, Berkshire) check that it covers all classes before trusting P/B or the yields. P/E uses EPS and is unaffected.
- **Small or negative equity** makes ROE and debt-to-equity extreme. Apple's ROE of about 170% is real: buybacks have shrunk its book equity.
- **Missing items blank the ratios that need them.** Apple stopped tagging interest expense after FY2023, so interest coverage is blank. The workflow prints a warning for any item that goes missing in the years shown.
- **Banks and insurers:** margins, liquidity, efficiency and FCF ratios don't apply to them (see the balance-sheet and cash-flow READMEs).

## Run it

```bash
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name your.email@example.com"
python main.py --ticker AAPL
python main.py --ticker AAPL --prices
python main.py --tickers AAPL,MSFT,GOOGL,NVDA --prices --category profitability,leverage,valuation
python main.py --list
python main.py --sample           # offline: no network or SEC_USER_AGENT needed
```

## Files

- `main.py`: entry point. Every ratio is defined in `quanttk/ratios/registry.py`.
- `requirements.txt`: pinned dependencies (yfinance only for `--prices`)
- `sample/aapl_facts.csv`: 90 Apple facts for fiscal 2023–2025 (the tag used for each line item, plus each year's original filing)
- `sample/aapl_prices.csv`: Apple's as-traded close on the three 10-K filing dates

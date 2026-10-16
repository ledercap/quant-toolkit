# Income statement: margins, growth and operating leverage

**Computes:** gross, operating and net margins, year-over-year growth in revenue, operating income and net income, and the degree of operating leverage, for any SEC filer, point-in-time as of any date.

**Inputs:** `RevenueFromContractWithCustomerExcludingAssessedTax` (or `Revenues` / `SalesRevenueNet` for older filings), `CostOfGoodsAndServicesSold`, `GrossProfit`, `OperatingIncomeLoss` and `NetIncomeLoss` (us-gaap XBRL facts, annual 10-K values) from [`data-sources/sec-edgar.md`](../../../data-sources/sec-edgar.md)

**Output:** a table by fiscal year, printed and written to `output/income_statement_<TICKER>.csv`

## Formula

For fiscal year *t*:

| Metric | Formula |
| --- | --- |
| Gross margin | GP<sub>t</sub> / Rev<sub>t</sub> |
| Operating margin | EBIT<sub>t</sub> / Rev<sub>t</sub> |
| Net margin | NI<sub>t</sub> / Rev<sub>t</sub> |
| Growth of X | g<sub>X,t</sub> = X<sub>t</sub> / X<sub>t−1</sub> − 1 |
| Degree of operating leverage (DOL) | DOL<sub>t</sub> = g<sub>EBIT,t</sub> / g<sub>Rev,t</sub> |

Where:
- **Rev** = revenue
- **GP** = gross profit (revenue minus cost of revenue when the filer doesn't report gross profit)
- **EBIT** = operating income (`OperatingIncomeLoss`)
- **NI** = net income attributable to the parent (`NetIncomeLoss`)

Sources:
- **Line items:** the FASB US GAAP Financial Reporting Taxonomy element definitions (https://xbrl.fasb.org), as exposed by the SEC XBRL APIs (https://www.sec.gov/search-filings/edgar-application-programming-interfaces).
- **Margin ratios:** standard common-size income statement ratios, as in CFA Institute, *International Financial Statement Analysis*, 4th ed. (2020), "Financial Analysis Techniques".
- **DOL:** the percentage change in operating income divided by the percentage change in sales, as in Brigham and Ehrhardt, *Financial Management: Theory and Practice*, 16th ed. (2020), chapter on capital structure decisions (business risk and operating leverage).

**Annual fact selection.** A fact counts as annual when its period lasts 350 to 380 days and it comes from a 10-K or 10-K/A. For each fiscal year end, the value from the latest filing with `filed` on or before `--as-of` is used. Later 10-Ks re-report prior years, so restated values replace originals, but only once they were public.

## Caveats

- **Tag changes:** companies change XBRL tags over time. Each line item tries several tags in priority order (see `CONCEPTS` in `main.py`), but unusual filers (banks, insurers, REITs) report revenue and gross profit differently. Expect blanks for them, not errors.
- **Restatements:** with `--as-of` set to today you see restated history. Set `--as-of` to a past date to see only what was known then, which avoids look-ahead bias in backtests.
- **DOL is unstable near zero growth:** the ratio divides by revenue growth, so it's left blank when revenue grew less than 1% (`MIN_GROWTH_FOR_DOL`). It's also hard to read when growth rates have opposite signs.
- **Fiscal years differ:** Apple's ends in late September, Microsoft's on June 30 and NVIDIA's in late January. Columns are labelled with the actual fiscal year-end date.
- **Units:** values are in USD as reported, shown in millions. Non-USD filers (20-F/40-F) aren't covered.
- **SEC access:** `SEC_USER_AGENT` must be set (name and email), and the SEC allows at most 10 requests per second.

## Run it

```bash
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name your.email@example.com"
python main.py --ticker AAPL
python main.py --ticker MSFT --as-of 2024-12-31 --years 8
python main.py --sample          # offline: no network or SEC_USER_AGENT needed
```

## Files

- `main.py`: entry point
- `requirements.txt`: pinned dependencies
- `sample/aapl_facts.csv`: 75 annual Apple facts (fiscal 2020 onward) for an offline run

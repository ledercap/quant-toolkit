# Cash flow: free cash flow, conversion, capex intensity and payouts

**Computes:** for any SEC filer, point-in-time as of any date:
- free cash flow (FCF) and FCF after stock-based compensation
- FCF margin, FCF conversion and operating cash flow relative to net income
- capex intensity and capex relative to depreciation
- stock-based compensation as a share of revenue
- dividends, buybacks and total cash returned to shareholders, relative to net income and to FCF
- FCF growth

These are also the main inputs for a later discounted-cash-flow (DCF) model.

**Inputs:** annual us-gaap XBRL amounts from 10-K filings: `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment` (or `PaymentsToAcquireProductiveAssets`), `DepreciationDepletionAndAmortization`, `ShareBasedCompensation`, `PaymentsOfDividends`, `PaymentsForRepurchaseOfCommonStock`, plus revenue, operating income and net income. All come from [`data-sources/sec-edgar.md`](../../../data-sources/sec-edgar.md). The full tag lists are in `quanttk/statements/concepts.py`.

**Output:** a table by fiscal year, printed and written to `output/cash_flow_<TICKER>.csv`, plus a warning for any line item that disappears after earlier years.

## Formula

For fiscal year *t*:

| Item | Formula |
| --- | --- |
| Free cash flow (FCF) | Cash from operations (CFO) − capital expenditure |
| FCF after SBC | FCF − stock-based compensation |
| FCF margin | FCF / revenue |
| FCF conversion | FCF / net income |
| CFO to net income | CFO / net income |
| Capex intensity | Capex / revenue |
| Capex to depreciation | Capex / depreciation and amortization |
| SBC to revenue | Stock-based compensation / revenue |
| Cash returned | Dividends paid + share buybacks |
| Payout ratio | Dividends / net income |
| Total payout ratio | (Dividends + buybacks) / net income |
| Cash returned to FCF | (Dividends + buybacks) / FCF |
| FCF growth | FCF<sub>t</sub> / FCF<sub>t−1</sub> − 1, blank when FCF<sub>t−1</sub> ≤ 0 |

Sources:
- **Cash flow ratios and FCF:** CFA Institute, *International Financial Statement Analysis*, 4th ed. (2020), "Financial Analysis Techniques" (cash flow ratios) and "Understanding Cash Flow Statements" (free cash flow).
- **FCF after SBC and capex relative to depreciation as a reinvestment gauge:** Koller, Goedhart and Wessels, *Valuation*, 7th ed. (2020), McKinsey & Company.
- **Line items:** FASB US GAAP Financial Reporting Taxonomy (https://xbrl.fasb.org).

**Point-in-time selection** is the same as the income-statement workflow: annual (350–380 day) facts from 10-K or 10-K/A filed on or before `--as-of`, latest filing per fiscal year.

## Caveats

- **Capex definition:** this uses gross purchases of property and equipment. Some companies report their own FCF net of asset-sale proceeds or incentives. Amazon does, so its self-reported FCF differs from this one.
- **Growth from a negative base is blank.** Amazon's 2022 FCF was negative, so 2023 FCF growth has no meaningful percentage and is left empty rather than shown as −290%.
- **Capex above depreciation** (above 1×) means the asset base is growing. Microsoft's capex of 3–3.4× D&A in FY2024–26 reflects its AI data-center build-out.
- **Banks and brokers:** operating cash flow swings with trading and lending balances, and capex is often not tagged, so FCF measures don't apply. JPM shows blanks and a volatile CFO-to-net-income ratio.
- **Missing items:** a company with no buybacks or dividends in a year often doesn't tag the line at all, so it shows blank and may trigger a warning ("either the balance is now zero or not disclosed...").
- **SEC access:** `SEC_USER_AGENT` must be set (name and email); at most 10 requests per second.

## Run it

```bash
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name your.email@example.com"
python main.py --ticker AAPL
python main.py --ticker AMZN --years 6
python main.py --sample          # offline: no network or SEC_USER_AGENT needed
```

## Files

- `main.py`: entry point. Calculations come from `quanttk.statements` and `quanttk.ratios`.
- `requirements.txt`: pinned dependencies
- `sample/aapl_facts.csv`: 65 annual Apple cash flow and income facts (fiscal 2021 onward, latest filing per fact) for an offline run

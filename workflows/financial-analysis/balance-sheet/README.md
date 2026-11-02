# Balance sheet: liquidity, leverage and working capital

**Computes:** for any SEC filer, point-in-time as of any date, from balances on each fiscal year-end date:
- working capital, total debt and net debt
- current, quick and cash ratios
- debt-to-equity, debt-to-assets, liabilities-to-assets and the equity multiplier
- working capital as a share of revenue

**Inputs:** us-gaap XBRL balances from 10-K filings: `CashAndCashEquivalentsAtCarryingValue`, `MarketableSecuritiesCurrent`, `AccountsReceivableNetCurrent`, `InventoryNet`, `AssetsCurrent`, `Assets`, `AccountsPayableCurrent`, `LiabilitiesCurrent`, `CommercialPaper`, `LongTermDebtCurrent`, `LongTermDebtNoncurrent`, `Liabilities`, `StockholdersEquity`, plus annual revenue to anchor fiscal year ends. All come from [`data-sources/sec-edgar.md`](../../../data-sources/sec-edgar.md). The full tag lists, with fallbacks, are in `quanttk/statements/concepts.py`.

**Output:** a table by fiscal year end, printed and written to `output/balance_sheet_<TICKER>.csv`, plus a warning for any line item that disappears after earlier years.

## Formula

At fiscal year end *t* (balances in USD):

| Item | Formula |
| --- | --- |
| Cash and investments | Cash and cash equivalents + current marketable securities |
| Total debt | Commercial paper + current portion of debt + long-term debt (missing parts count as 0) |
| Net debt | Total debt − cash and investments |
| Working capital | Current assets − current liabilities |
| Current ratio | Current assets / current liabilities |
| Quick ratio | (Cash and investments + receivables) / current liabilities |
| Cash ratio | Cash and investments / current liabilities |
| Debt-to-equity | Total debt / shareholders' equity |
| Debt-to-assets | Total debt / total assets |
| Liabilities-to-assets | Total liabilities / total assets |
| Equity multiplier | Total assets / shareholders' equity |
| Working capital to revenue | Working capital / annual revenue for the fiscal year |

Sources:
- **Balance-sheet line items:** FASB US GAAP Financial Reporting Taxonomy element definitions (https://xbrl.fasb.org).
- **Liquidity and solvency ratios:** CFA Institute, *International Financial Statement Analysis*, 4th ed. (2020), "Financial Analysis Techniques".
- **Net debt:** Damodaran, A., *Investment Valuation*, 3rd ed. (2012).

**Point-in-time selection.** A balance counts when it is an instant fact (no period start), dated on a fiscal year-end, and reported in a 10-K or 10-K/A filed on or before `--as-of`. Fiscal year-ends are the end dates of the company's annual (350–380 day) facts. For each year-end the latest such filing wins, so restated balances replace originals only once they were public.

## Caveats

- **Company-specific tags disappear.** SEC company facts include only standard us-gaap tags. When a filer moves a line to its own tag, the item goes missing. Example: NVIDIA's current marketable securities for FY2026 (cash and investments then shows $10.6bn instead of roughly $30bn). The workflow prints a warning whenever an item reported in earlier years is missing, so a gap is never silently treated as zero.
- **Banks, insurers and brokers** don't present a classified balance sheet (no current assets or liabilities), so liquidity ratios and working capital are blank for them (try JPM). Their "debt" also excludes deposits, which are their main funding, so leverage ratios aren't comparable with industrial companies.
- **Leases:** total debt excludes operating lease liabilities. Add them if you want lease-adjusted leverage.
- **Negative working capital** isn't always weakness. Apple runs negative working capital because suppliers fund its inventory (see the cash conversion cycle in the ratios workflow).
- **Units:** USD, as reported, shown in millions. Non-USD filers (20-F/40-F) aren't covered.
- **SEC access:** `SEC_USER_AGENT` must be set (name and email); at most 10 requests per second.

## Run it

```bash
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name your.email@example.com"
python main.py --ticker AAPL
python main.py --ticker NVDA --years 3      # shows the missing-tag warning
python main.py --sample                     # offline: no network or SEC_USER_AGENT needed
```

## Files

- `main.py`: entry point. Calculations come from `quanttk.statements` and `quanttk.ratios`.
- `requirements.txt`: pinned dependencies
- `sample/aapl_facts.csv`: 85 Apple facts (fiscal 2021 onward, latest filing per fact) for an offline run

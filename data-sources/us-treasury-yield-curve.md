# US Treasury Daily Par Yield Curve

**Covers:** Official daily par yield curve rates for US Treasury securities at 1, 1.5, 2, 3, 4 and 6 months and 1, 2, 3, 5, 7, 10, 20 and 30 years. The same page also publishes bill rates, long-term rates and real (TIPS) yield curve rates. Nominal par yields go back to 1990.

**Provider:** U.S. Department of the Treasury | **Docs:** https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve (XML feed: https://home.treasury.gov/treasury-daily-interest-rate-xml-feed)

## Access

- **Method:** bulk download. Year-by-year CSV and an XML feed from `home.treasury.gov`, no client library needed.
- **Auth:** none. Env var name: not applicable.
- **Rate limits:** unknown, none published. One request per year of history is enough.
- **Formats:** CSV, XML

## Cost

- **Free tier:** everything
- **Paid tiers:** none
- **License or terms:** US government work, in the public domain

## Quality notes

- **Update frequency:** daily, on business days, usually by late afternoon ET
- **Known gaps:** tenor columns changed over time: the 2-month started in 2018, the 4-month in 2022 and the 1.5-month in 2025, and the 20-year had a gap from 1987 to 1993. Older rows have blanks in those columns. These are par yields fitted by Treasury's curve model, not traded quotes. Dates are in `MM/DD/YYYY` format.
- **Point-in-time?** yes in practice. Rates are published once a day and very rarely revised.

## Minimal example

```python
import pandas as pd

year = 2026
url = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    f"daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
    f"&field_tdr_date_value={year}&page&_format=csv"
)
curve = pd.read_csv(url, parse_dates=["Date"]).set_index("Date").sort_index()
print(curve[["3 Mo", "2 Yr", "10 Yr"]].tail())
```

## Used by

- `workflows/options/greeks` (planned: risk-free rate by tenor)

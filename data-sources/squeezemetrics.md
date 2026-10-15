# SqueezeMetrics DIX and GEX

**Covers:** Two daily S&P 500 market-structure indicators. DIX (Dark Index) is a dollar-weighted measure of short-sale volume in dark pools across S&P 500 stocks. GEX (Gamma Exposure) estimates the dollar gamma that options dealers hold on the S&P 500. Each row also has the S&P 500 close. History starts in May 2011.

**Provider:** SqueezeMetrics | **Docs:** https://squeezemetrics.com/monitor/dix (methodology papers linked from that page)

## Access

- **Method:** bulk download, one CSV with the full history at `https://squeezemetrics.com/monitor/static/DIX.csv`
- **Auth:** none. Env var name: not applicable.
- **Rate limits:** unknown. The file is updated once a day, so download it once a day.
- **Formats:** CSV with columns `date, price, dix, gex`

## Cost

- **Free tier:** the DIX and GEX history CSV
- **Paid tiers:** paid SqueezeMetrics subscriptions add single-stock gamma, more indicators and tools. Prices are listed on their site.
- **License or terms:** unknown. No license is published for the free CSV. Treat it as free for personal research only and don't redistribute it.

## Quality notes

- **Update frequency:** daily, after the US close
- **Known gaps:** GEX is a model estimate. It assumes customers buy calls and sell puts, so dealers are on the other side; SqueezeMetrics doesn't observe real dealer positions. Index level only, no single-stock or strike-level data. The methodology can change without notice.
- **Point-in-time?** unknown. History may be recomputed when the method changes.

## Minimal example

```python
import pandas as pd

dix = pd.read_csv("https://squeezemetrics.com/monitor/static/DIX.csv", parse_dates=["date"])
print(dix.tail())  # gex is in dollars of S&P 500 exposure per 1% move
```

## Used by

- `workflows/options/gamma` (planned: benchmark for a home-built GEX calculation)

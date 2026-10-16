# yfinance (Yahoo Finance)

**Covers:** Global stocks, ETFs, indexes, mutual funds, FX, crypto and futures from Yahoo Finance. Daily bars back to listing (decades for large US stocks), intraday bars (1-minute for the last 7 days, longer intervals up to 60 or 730 days), dividends and splits, current options chains with IV and open interest, financial statements (4 annual and 4 quarterly periods), holders, analyst estimates and calendars.

**Provider:** Open-source Python package by Ran Aroussi and contributors, which scrapes Yahoo Finance. Not affiliated with Yahoo. | **Docs:** https://ranaroussi.github.io/yfinance/ and https://github.com/ranaroussi/yfinance

## Access

- **Method:** Python package (`pip install yfinance`)
- **Auth:** none. Env var name: not applicable.
- **Rate limits:** unknown. Yahoo throttles heavy use and returns `YFRateLimitError` or empty data. Batch tickers with `yf.download` and cache the results.
- **Formats:** pandas DataFrames

## Cost

- **Free tier:** everything
- **Paid tiers:** none (Yahoo Finance Gold is a website subscription, not API access)
- **License or terms:** the package is Apache 2.0, but the data is governed by Yahoo's terms, which allow personal use only. Not for commercial use or redistribution.

## Quality notes

- **Update frequency:** near real time for quotes on most US listings, end-of-day for bars
- **Known gaps:** unofficial. It breaks when Yahoo changes its site, so pin the version and expect updates. No delisted tickers, which means survivorship bias. Statements cover only the last 4 years or quarters. Options chains are current only, with no Greeks besides IV. Bars are adjusted by default (`auto_adjust=True`).
- **Point-in-time?** no

## Minimal example

```python
import yfinance as yf

prices = yf.download(["SPY", "AAPL"], start="2026-01-01", auto_adjust=True, progress=False)
print(prices["Close"].tail())

spy = yf.Ticker("SPY")
calls = spy.option_chain(spy.options[0]).calls
print(calls[["strike", "bid", "ask", "impliedVolatility", "openInterest"]].head())
```

## Used by

- Prototyping only. Swap in a licensed source before anything depends on it.

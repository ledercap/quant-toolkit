# Data and API library

One file per source. Copy `_TEMPLATE.md`, name the file after the source in lowercase with hyphens (for example `sec-edgar.md`, `fred.md`, `cboe-options.md`), and fill every field.

## Index

| Source | Covers | Access | Cost | File |
| --- | --- | --- | --- | --- |
| Alpha Vantage | Stocks, FX, crypto, commodities, fundamentals, indicators | REST, API key | Free 25/day; paid from $49.99/mo | [alpha-vantage.md](alpha-vantage.md) |
| Cboe delayed quotes | Options chains with IV and Greeks, 15-min delayed | Undocumented JSON, no key | Free (personal use) | [cboe-delayed-quotes.md](cboe-delayed-quotes.md) |
| CFTC Commitments of Traders | Weekly futures positioning by trader type | Socrata REST, no key | Free | [cftc-commitments-of-traders.md](cftc-commitments-of-traders.md) |
| CoinGecko | Crypto prices, market cap, volume | REST, demo key | Free demo; paid from $35/mo | [coingecko.md](coingecko.md) |
| Databento | Exchange tick data: CME futures, OPRA options, US equities | Python client / REST, API key | $125 free credit; usage-based or from $199/mo | [databento.md](databento.md) |
| ECB Data Portal | EUR FX reference rates, euro area rates and macro | SDMX REST, no key | Free | [ecb-data-portal.md](ecb-data-portal.md) |
| EIA Open Data | Oil and gas prices, inventories, production | REST, API key | Free | [eia.md](eia.md) |
| Financial Modeling Prep | Standardized fundamentals, estimates, transcripts | REST, API key | Free 250/day; paid from $22/mo | [financial-modeling-prep.md](financial-modeling-prep.md) |
| FINRA short sale volume | Daily off-exchange short volume by symbol | Bulk text files, no key | Free | [finra-short-sale-volume.md](finra-short-sale-volume.md) |
| FRED | US and global macro, rates, spreads, with revision history (ALFRED) | REST, API key | Free | [fred.md](fred.md) |
| Massive (formerly Polygon.io) | US stocks, options with Greeks, indexes, FX, crypto | REST / WebSocket / flat files, API key | Free EOD; paid from $29/mo per asset class | [massive.md](massive.md) |
| SEC EDGAR | Filings and XBRL financial statement facts | REST / bulk ZIP, User-Agent only | Free | [sec-edgar.md](sec-edgar.md) |
| SqueezeMetrics DIX and GEX | S&P 500 dark-pool index and dealer gamma estimate | CSV download, no key | Free CSV | [squeezemetrics.md](squeezemetrics.md) |
| Tradier | Quotes, bars, options chains with ORATS Greeks | REST / streaming, bearer token | Free sandbox; real-time with brokerage account | [tradier.md](tradier.md) |
| US Treasury yield curve | Daily par yields, 1 month to 30 years | CSV / XML download, no key | Free | [us-treasury-yield-curve.md](us-treasury-yield-curve.md) |
| yfinance | Global prices, options chains, basic statements | Python package, no key | Free (personal use, unofficial) | [yfinance.md](yfinance.md) |

Keep this table in alphabetical order and add a row whenever you add a file.

## Coverage we want

Filings, fundamentals, prices, options chains, implied volatility, gamma exposure and dealer positioning, futures, commodities and oil, macro and rates, FX, crypto, alternative data.

## Coverage map

Which sources to reach for, by data type. The **first** source listed is the recommended starting point. Every area in "Coverage we want" has at least one source, and every area has a **free** option (marked *free*).

| Coverage | Sources | Free option | Gaps to fill |
| --- | --- | --- | --- |
| Filings | **SEC EDGAR** | SEC EDGAR | Non-US filings |
| Fundamentals | **SEC EDGAR** (as reported, point-in-time), Financial Modeling Prep (standardized), Alpha Vantage, yfinance | SEC EDGAR | Free point-in-time standardized fundamentals |
| Prices | **Massive**, Tradier, Alpha Vantage, yfinance, Databento | yfinance (personal use), Massive end-of-day | Free survivorship-bias-free history |
| Options chains | **Cboe delayed quotes**, Tradier, Massive, yfinance, Databento (OPRA) | Cboe delayed quotes | Free historical chains |
| Implied volatility | **Cboe delayed quotes**, Tradier (ORATS), Massive | Cboe delayed quotes | Historical IV surfaces |
| Gamma exposure and dealer positioning | **SqueezeMetrics** (index level), Cboe delayed quotes (build strike-level GEX yourself) | Both | Single-stock GEX history, real dealer positions |
| Futures | **CFTC COT** (positioning), yfinance (continuous front-month prices such as `CL=F`), Databento (exchange prices and ticks) | CFTC COT, yfinance | Licensed free futures price history |
| Commodities and oil | **EIA**, CFTC COT, Alpha Vantage, Databento | EIA, CFTC COT | Metals and agriculture fundamentals |
| Macro and rates | **FRED**, US Treasury yield curve, ECB Data Portal | All three | Non-US/EU central banks |
| FX | **ECB Data Portal**, FRED, Alpha Vantage, Massive | ECB Data Portal, FRED | Intraday FX |
| Crypto | **CoinGecko**, Massive, Alpha Vantage | CoinGecko (demo key) | On-chain data, exchange-level order books |
| Alternative data | **FINRA short sale volume**, SqueezeMetrics DIX | Both | Sentiment, web traffic, satellite |

## API keys and environment variables

Keys live in a local `.env` file (already gitignored) and are read from the environment. Never paste a key into an entry. Sources not listed here need no key.

| Env var | Source | Needed for | Get it at | Cost |
| --- | --- | --- | --- | --- |
| `SEC_USER_AGENT` | SEC EDGAR | Required on every request (your name and email, not a key) | No sign-up: set it to e.g. `Jane Doe jane@example.com` | Free |
| `FRED_API_KEY` | FRED | All requests | https://fred.stlouisfed.org/docs/api/api_key.html | Free |
| `EIA_API_KEY` | EIA | All requests (`DEMO_KEY` works for a few test calls) | https://www.eia.gov/opendata/register.php | Free |
| `COINGECKO_API_KEY` | CoinGecko | Demo plan | https://www.coingecko.com/en/api/pricing | Free demo |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage | All requests | https://www.alphavantage.co/support/#api-key | Free (25/day) |
| `FMP_API_KEY` | Financial Modeling Prep | All requests | https://site.financialmodelingprep.com/developer/docs | Free (250/day) |
| `MASSIVE_API_KEY` | Massive | All requests | https://massive.com/pricing | Free end-of-day tier |
| `TRADIER_API_KEY` | Tradier | All requests (sandbox token for delayed data) | https://developer.tradier.com | Free sandbox |
| `DATABENTO_API_KEY` | Databento | All requests | https://databento.com/signup | $125 free credit, then paid |
| `CFTC_APP_TOKEN` | CFTC COT | Optional: higher rate limits | https://publicreporting.cftc.gov/signup | Free |
| `FINRA_API_KEY` | FINRA | Optional: only for the FINRA Query API, not the daily files | https://developer.finra.org | Free |

Python packages used by the minimal examples (Python 3.11+):

```bash
pip install requests pandas yfinance databento
```

## Review log

Every entry was checked against the provider's own docs and pricing pages. For each batch, the log records whether each **minimal example ran successfully**. Re-check costs and limits before relying on them, because providers change them often.

**Batch 1, 2026-10-14** (16 sources)

| File | Example ran? | Notes for reviewers |
| --- | --- | --- |
| alpha-vantage.md | No, needs key | Endpoint confirmed with the `demo` key |
| cboe-delayed-quotes.md | Yes | Undocumented endpoint; may change without notice |
| cftc-commitments-of-traders.md | Yes | |
| coingecko.md | No, needs key | Endpoint confirmed without a key |
| databento.md | No, needs key | Uses paid credits; the example prints a cost estimate first |
| ecb-data-portal.md | Yes | |
| eia.md | Yes, with `DEMO_KEY` | |
| financial-modeling-prep.md | No, needs key | Prices taken from FMP and third-party listings; confirm on the FMP pricing page |
| finra-short-sale-volume.md | Yes | CDN blocks Python's default user agent; example works around it |
| fred.md | No, needs key | |
| massive.md | No, needs key | Base URL confirmed (returns 401 without a key) |
| sec-edgar.md | Yes | Needs `SEC_USER_AGENT` set |
| squeezemetrics.md | Yes | License for the free CSV is not published |
| tradier.md | No, needs key | Real-time account requirements unconfirmed |
| us-treasury-yield-curve.md | Yes | |
| yfinance.md | Yes | Unofficial; pin the version |

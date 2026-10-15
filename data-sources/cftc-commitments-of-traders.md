# CFTC Commitments of Traders (COT)

**Covers:** Weekly open interest and long and short positions by trader category for every US futures market with enough reportable traders: commodities (crude oil, natural gas, metals, grains, livestock), interest rates, equity indexes, currencies and VIX. History goes back to 1986 (the Legacy report).

**Provider:** U.S. Commodity Futures Trading Commission | **Docs:** https://publicreporting.cftc.gov/stories/s/r4w3-av2u

## Access

- **Method:** REST through the Socrata Open Data API (SODA) at `https://publicreporting.cftc.gov/resource/<dataset-id>.json`. Queries use SoQL (`$select`, `$where`, `$order`, `$limit`).
- **Dataset IDs:**
  - Legacy: `6dca-aqww` (futures only), `jun7-fc8e` (futures and options combined)
  - Disaggregated: `72hh-3qpy` (futures only), `kh3c-gbw2` (combined)
  - Traders in Financial Futures (TFF): `gpe5-46if` (futures only), `yw9f-hn96` (combined)
  - Commodity Index Traders supplement: `4zgm-a668`
- **Auth:** none required. An optional Socrata app token raises your throttling limit; send it in the `X-App-Token` header. Env var name: `CFTC_APP_TOKEN`
- **Rate limits:** Socrata throttles anonymous requests by IP and does not publish a fixed number. An app token removes most throttling.
- **Formats:** JSON, CSV (`.csv`), GeoJSON

## Cost

- **Free tier:** everything
- **Paid tiers:** none
- **License or terms:** US government work, in the public domain

## Quality notes

- **Update frequency:** weekly. Positions as of Tuesday are released Friday at 3:30 p.m. ET, delayed to the following business day after federal holidays.
- **Known gaps:** positions are 3 days old when published. Market names change over time (for example `CRUDE OIL, LIGHT SWEET` became `WTI-PHYSICAL`), so filter on `cftc_contract_market_code` (for example `067651` for NYMEX WTI), not on the name. Every field arrives as a string. Category definitions differ between Legacy, Disaggregated and TFF, so don't mix them in one series. One field is misspelled in the source (`noncomm_postions_spread_all`).
- **Point-in-time?** yes in practice. Each weekly report is a snapshot and corrections are rare.

## Minimal example

```python
import requests

params = {
    "$select": "report_date_as_yyyy_mm_dd,market_and_exchange_names,open_interest_all,"
               "noncomm_positions_long_all,noncomm_positions_short_all",
    "$where": "cftc_contract_market_code='067651'",  # NYMEX WTI crude oil
    "$order": "report_date_as_yyyy_mm_dd DESC",
    "$limit": 5,
}
r = requests.get("https://publicreporting.cftc.gov/resource/6dca-aqww.json", params=params, timeout=30)
for row in r.json():
    net = int(row["noncomm_positions_long_all"]) - int(row["noncomm_positions_short_all"])
    print(row["report_date_as_yyyy_mm_dd"][:10], "OI", row["open_interest_all"], "speculator net", net)
```

## Used by

- `sectors/` commodities and oil coverage (planned)

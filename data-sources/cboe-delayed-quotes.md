# Cboe delayed option quotes

**Covers:** Full options chains for US equities, ETFs and indexes (SPX, VIX, SPY, single stocks), delayed 15 minutes. Each contract comes with bid and ask, sizes, last trade, volume, open interest, implied volatility, delta, gamma, vega, theta and rho. Also returns the underlying's quote. Current snapshot only, no history.

**Provider:** Cboe Global Markets | **Docs:** none. This is the JSON feed behind the delayed-quotes pages on https://www.cboe.com/delayed_quotes/ and isn't a documented API.

## Access

- **Method:** REST, `https://cdn.cboe.com/api/global/delayed_quotes/options/<SYMBOL>.json`. Indexes take an underscore prefix (`_SPX`, `_VIX`). The CDN can redirect, so follow redirects and send a browser-style `User-Agent`.
- **Auth:** none. Env var name: not applicable.
- **Rate limits:** unknown. Unofficial endpoint, so keep requests low (one per symbol every few minutes).
- **Formats:** JSON

## Cost

- **Free tier:** the delayed chains above
- **Paid tiers:** official data comes through Cboe DataShop (https://datashop.cboe.com) and Cboe LiveVol, priced per dataset. That's where to get historical chains and end-of-day Greeks.
- **License or terms:** covered by the Cboe website legal terms (https://www.cboe.com/legal/). There is no published permission for automated access or redistribution, so treat it as personal, non-commercial research only.

## Quality notes

- **Update frequency:** about every 15 minutes during market hours (15-minute delay)
- **Known gaps:** undocumented, so field names and URLs can change or disappear without warning. Option symbols are OCC-style strings (`SPY261016C00550000`) that you must parse into expiry, type and strike. Implied vol and Greeks come back as `0.0` for deep in-the-money and illiquid contracts. No history, so you must snapshot it yourself to build one.
- **Point-in-time?** yes for each snapshot, which carries a `timestamp`. No history is provided.

## Minimal example

```python
import pandas as pd
import requests

url = "https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json"
data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).json()["data"]

chain = pd.DataFrame(data["options"])
chain["expiry"] = pd.to_datetime(chain["option"].str[-15:-9], format="%y%m%d")
chain["type"] = chain["option"].str[-9]
chain["strike"] = chain["option"].str[-8:].astype(int) / 1000
print("spot", data["current_price"])
print(chain[["expiry", "type", "strike", "bid", "ask", "iv", "gamma", "open_interest"]].head())
```

## Used by

- `workflows/options/gamma` (planned: strike-level gamma exposure)
- `workflows/options/greeks` (planned)
- `workflows/options/volume` (planned)

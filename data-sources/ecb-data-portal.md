# ECB Data Portal

**Covers:** Euro area statistics from the European Central Bank: daily euro foreign exchange reference rates against about 30 currencies (since 1999), ECB policy rates, €STR, euro area yield curves, money supply, bank lending, inflation (HICP) and balance of payments.

**Provider:** European Central Bank | **Docs:** https://data.ecb.europa.eu/help/api/overview

## Access

- **Method:** REST in the SDMX 2.1 standard at `https://data-api.ecb.europa.eu/service/data/<flow>/<key>`. A key is the series dimensions joined by dots. For example `EXR/D.USD.EUR.SP00.A` is the daily USD per EUR reference rate.
- **Auth:** none. Env var name: not applicable.
- **Rate limits:** unknown, none published
- **Formats:** CSV (`format=csvdata`), SDMX-JSON (`format=jsondata`), SDMX-ML (XML, the default)

## Cost

- **Free tier:** everything
- **Paid tiers:** none
- **License or terms:** free reuse with attribution to the ECB as the source (https://www.ecb.europa.eu/services/disclaimer/html/index.en.html)

## Quality notes

- **Update frequency:** FX reference rates come out daily at around 16:00 CET on TARGET business days. Other series follow their release calendars.
- **Known gaps:** reference rates are one daily fixing at 14:15 CET, not tradable quotes and not intraday. No rates on TARGET holidays. Every rate is quoted as foreign currency per euro, so you must invert or cross them for other pairs.
- **Point-in-time?** yes for FX reference rates, which are never revised. Revised for macro series.

## Minimal example

```python
import pandas as pd

url = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=5&format=csvdata"
fx = pd.read_csv(url)
print(fx[["TIME_PERIOD", "OBS_VALUE"]])  # US dollars per euro
```

## Used by

- FX workflows (planned)

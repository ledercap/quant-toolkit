# Options volatility: term structure, skew, realized vs implied, VIX replication

**Computes:** from a Cboe options chain:
- **Term structure:** at-the-money implied volatility (IV) by expiry, and forward volatility between consecutive expiries.
- **Skew:** IV of the 25-delta call and 25-delta put per expiry, the risk reversal and the butterfly.
- **Smile:** IV and log-moneyness for every out-of-the-money contract.
- **Realized volatility:** annualized close-to-close volatility of the underlying over 10, 21 and 63 trading days.
- **Volatility risk premium:** 30-day ATM implied minus 21-day realized.
- **VIX replication (SPX only):** the VIX recomputed from the SPX chain with Cboe's own method and compared with the published VIX. That end-to-end check validates the whole pipeline.

**Inputs:**
- Option bid/ask, spot and snapshot time from [`data-sources/cboe-delayed-quotes.md`](../../../data-sources/cboe-delayed-quotes.md), plus the published VIX from the same feed.
- Par yields from [`data-sources/us-treasury-yield-curve.md`](../../../data-sources/us-treasury-yield-curve.md).
- Daily closes of the underlying (adjusted) from [`data-sources/yfinance.md`](../../../data-sources/yfinance.md), for realized volatility only.

**Output:** printed tables, plus `output/term_structure_<SYMBOL>.csv`, `output/skew_<SYMBOL>.csv` and `output/surface_<SYMBOL>.csv` (every priced contract).

## Formula

**Implied volatility.** Identical to the Greeks workflow (`quanttk.options.surface`): Black-76 IV from the bid/ask mid on a put-call-parity forward, with Treasury rates converted to continuous compounding. The formulas and citations are in [`workflows/options/greeks/README.md`](../greeks/README.md). When an expiry date lists both AM-settled SPX and PM-settled SPXW, SPXW is used for the term structure and skew.

**Smile.** Only out-of-the-money options are used: puts with K < F and calls with K ≥ F. They're the liquid side, and by put-call parity they carry the same information as in-the-money ones. Log-moneyness is k = ln(K / F). (Hull, *Options, Futures, and Other Derivatives*, 11th ed. (2021), "Volatility Smiles".)

**ATM IV** = the smile interpolated linearly in strike at K = F.

**Forward volatility** between expiries 1 and 2, from the additivity of variance (Hull):

σ<sub>fwd</sub>² = (σ₂² T₂ − σ₁² T₁) / (T₂ − T₁)

**Constant-maturity IV** (the 30-day figure) interpolates total variance σ²T linearly in T.

**Skew.**
- IV at a delta is interpolated linearly in BSM delta across the OTM calls (for +0.25) or puts (for −0.25).
- Risk reversal RR₂₅ = IV(25Δ call) − IV(25Δ put). Negative means puts are priced richer than calls, the normal shape for equity indexes.
- Butterfly BF₂₅ = ½ [IV(25Δ call) + IV(25Δ put)] − IV<sub>ATM</sub>, which measures the curvature of the smile.

(Standard FX/equity-options quoting conventions; see Hull, "Volatility Smiles".)

**Realized volatility.** σ<sub>N</sub> = √252 × stdev(ln(P<sub>t</sub>/P<sub>t−1</sub>)) over the last N daily returns (sample standard deviation). (Sinclair, E., *Volatility Trading*, 2nd ed. (2013), ch. 2.)

**Volatility risk premium** = 30-day ATM IV − 21-day realized volatility.

**VIX replication** (Cboe Volatility Index Mathematics Methodology, https://cdn.cboe.com/api/global/us_indices/governance/Cboe_Volatility_Index_Mathematics_Methodology.pdf):
1. **Choose two expiries.** Near and next term are the expiries with 23–37 days to settlement that bracket 30 days. When both SPX and SPXW list a date, the standard SPX series is used. T is in minutes to settlement / 525,600.
2. **Forward.** Per term, F = K\* + e^{RT}(C − P) at the strike K\* where |C − P| is smallest. K₀ is the first strike at or below F.
3. **Strike strip.** Take out-of-the-money puts below K₀ and calls above K₀, moving outward and stopping after two consecutive zero bids. At K₀, Q is the average of the put and call mids. ΔK<sub>i</sub> = (K<sub>i+1</sub> − K<sub>i−1</sub>)/2, one-sided at the ends.
4. **Variance per term:** σ² = (2/T) Σ ΔK<sub>i</sub>/K<sub>i</sub>² e^{RT} Q(K<sub>i</sub>) − (1/T)(F/K₀ − 1)².
5. **Interpolate to 30 days:** VIX = 100 √{ [T₁σ₁² (N₂ − N₃₀)/(N₂ − N₁) + T₂σ₂² (N₃₀ − N₁)/(N₂ − N₁)] × N₃₆₅ / N₃₀ }, where N is minutes.

## Results on a live snapshot (2026-10-22, after the close)

- **VIX replication:** **19.00** vs Cboe's published **19.03**, a difference of 0.03 points. Near term SPX 2026-11-20 (28.6 days, 475 strikes); next term SPXW 2026-11-23 (31.9 days, 115 strikes).
- **30-day ATM IV** 14.6%, **21-day realized** 9.7%: a volatility risk premium of +4.9 points.
- **25-delta risk reversal** from −2.6 points at 1 day to −5.4 points at 28 days: put skew steepens with maturity.

## Caveats

- **Calendar time.** T counts calendar days, so a weekend inside an interval shows up as low forward volatility (for example 0.09–0.10 for the intervals spanning a weekend) and the next interval as high. Trading-day time would smooth this. The VIX method also uses calendar minutes, which is why the replication matches.
- **VIX rate and timing.** Cboe interpolates Treasury rates with a cubic spline; this uses linear interpolation, worth a few hundredths of a point at most. The published VIX is calculated live during the session. Compare snapshots taken at the same time, ideally after the 16:15 ET close as here.
- **Mid prices:** wide or one-sided markets give unreliable IVs. Contracts with no bid are excluded from the surface. The VIX strip follows Cboe's zero-bid rule instead.
- **American-style options** (SPY, single stocks) carry an early-exercise premium that Black-76 ignores. IVs, especially deep in-the-money ones, are slightly off. SPX is European.
- **Realized volatility prices** come from yfinance (personal use only). The implied side doesn't depend on them, and if the download fails the workflow continues without realized volatility.
- **Delay:** the data is 15 minutes delayed and snapshot-only. Use the volume workflow's snapshot archive to build history.

## Run it

```bash
pip install -r requirements.txt
python main.py                          # SPX, with the VIX replication
python main.py --symbol SPY --max-days 90
python main.py --sample                 # offline: 90 SPXW contracts across 3 expiries
```

## Files

- `main.py`: entry point. Calculations come from `quanttk.options.surface` and `quanttk.options.volatility`.
- `requirements.txt`: pinned dependencies
- `sample/chain.csv`: 90 SPXW contracts (15 strikes within ±5% of spot, for the expiries about 7, 22 and 50 days out), with spot and snapshot time
- `sample/yield_curve.csv`: the Treasury par curve for the same date
- `sample/closes.csv`: 70 daily S&P 500 closes for realized volatility

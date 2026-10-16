# Gamma exposure (GEX): by strike, total, walls, gamma flip and sensitivity range

**Computes:** estimated dealer gamma exposure from an options chain:
- dollar GEX per 1% move, by strike and in total
- the call wall and put wall (strikes with the largest call and put GEX)
- the gamma flip: the spot level where total GEX changes sign, with IVs held fixed
- a sensitivity report: total GEX under five assumptions (plus SqueezeMetrics for SPX), with the range, the median and whether the sign is consistent

**Inputs:**
- Option `iv`, `gamma` and `open_interest`, plus spot and snapshot time, from [`data-sources/cboe-delayed-quotes.md`](../../../data-sources/cboe-delayed-quotes.md)
- The daily SPX GEX from [`data-sources/squeezemetrics.md`](../../../data-sources/squeezemetrics.md), as one point in the SPX sensitivity range

**Output:** a printed summary, plus three files in `output/`:
- `gex_by_strike_<SYMBOL>.csv`: call, put and net GEX per strike
- `gex_profile_<SYMBOL>.csv`: total GEX at hypothetical spot levels from −15% to +15%
- `gex_sensitivity_<SYMBOL>.csv`: total GEX under each assumption

## Formula

For each contract *i* with open interest OIᵢ and gamma Γᵢ, at spot S:

GEXᵢ = sᵢ · Γᵢ · OIᵢ · 100 · S · (0.01 · S)

- **Dealer sign:** sᵢ = +1 for calls and −1 for puts. This is the SqueezeMetrics convention: customers are assumed to buy calls and buy puts, so dealers are long calls and short puts (SqueezeMetrics, "Gamma Exposure (GEX)" white paper, https://squeezemetrics.com/download/white_paper.pdf).
- **The terms:** Γᵢ · S · 0.01 is the change in delta for a 1% move. Multiplying by 100 shares per contract and by S turns it into dollars.
- **Per strike:** GEX(K) = Σ GEXᵢ over contracts with strike K, across all expiries. Total GEX = Σᵢ GEXᵢ.
- **Call wall** = argmax over K of call GEX(K). **Put wall** = argmin over K of put GEX(K).

**Gamma per contract.** Gamma is recomputed with Black-Scholes from Cboe's implied volatility σᵢ, with the rate set equal to the dividend yield (forward = spot):

Γᵢ = φ(d₁) / (S σᵢ √T), d₁ = [ln(S/K) + σᵢ²T/2] / (σᵢ√T)

(Hull, J. C., *Options, Futures, and Other Derivatives*, 11th ed. (2021), chapter "The Greek Letters".) Cboe's published gamma is used only for contracts without an IV.

**Gamma flip.**
1. Recompute total GEX(S′) on a grid S′ = S × (0.85, 0.8525, …, 1.15), holding each contract's IV and time to expiry fixed.
2. The flip is the zero crossing nearest to spot, found by linear interpolation.
3. Contracts without an IV can't be repriced, so their GEX is held constant across the grid.

**Sensitivity range and median.** Total GEX is recomputed under each assumption about which contracts drive dealer hedging:

| Assumption | Contracts included | Why it's defensible |
| --- | --- | --- |
| Base | All expiries | The standard definition |
| Excluding 0–1 day expiries | T > 1 day | Open interest is a day old, so same-day positioning isn't known |
| Excluding contracts with no IV | Cboe IV > 0 | Only contracts with precise model gamma |
| Expiries ≤ 90 days | T ≤ 90 days | Near-term hedging dominates daily flows |
| Expiries > 7 days | T > 7 days | Leaves out the most volatile, fastest-changing front week |
| SqueezeMetrics (SPX only) | Their published figure | An independent method, with proprietary adjustments |

The report gives the **range** (minimum to maximum), the **median** and a **sign verdict**: "consistent" if every estimate has the same sign, "uncertain" if the range crosses zero. The median is the headline estimate because one extreme assumption can't pull it far. The range shows how much the answer depends on choices that can't be observed.

## Results on a live snapshot (2026-10-16, after the close)

| | SPX | SPY | QQQ |
| --- | --- | --- | --- |
| **Median total GEX (headline)** | **−$4.25 bn** | **−$8.16 bn** | **−$9.01 bn** |
| Range across assumptions | −$10.90 to +$8.12 bn | −$8.31 to −$3.83 bn | −$9.56 to −$5.38 bn |
| Sign verdict | **Uncertain** (range crosses zero) | Consistently negative | Consistently negative |
| Base total GEX (all expiries) | −$7.73 bn | −$8.31 bn | −$9.56 bn |
| Gross call / put GEX | +$302 bn / −$310 bn | +$22 bn / −$30 bn | +$10 bn / −$20 bn |
| Gamma flip | 7,751 (+0.1%) | 776 (+0.5%) | 740 (+2.2%) |
| Base total with Cboe's rounded gamma | +$9.22 bn | −$6.91 bn | −$7.46 bn |
| SqueezeMetrics SPX GEX (2026-10-15) | +$6.02 bn (in the range) | | |

## Caveats

- **Net GEX is a small difference of large numbers.** For SPX it's about 2.5% of gross call or put GEX, so a small change in assumptions can flip its sign. That's why the headline is the median of the sensitivity range, reported with the range and sign verdict, not a single total. When the verdict is "uncertain", don't trade on the sign; the strike-level picture, the walls and the location of the flip are more robust.
- **Dealer positioning is assumed, not observed.** Open interest doesn't say who is long. The "dealers long calls, short puts" rule is a convention and is wrong for, say, overwriting funds that sell calls. That's the main reason the base total doesn't match SqueezeMetrics, whose adjustments are proprietary; their figure is included in the SPX range for comparison rather than treated as the right answer.
- **Cboe rounds gamma to 4 decimals.** For SPX, near-the-money gammas are around 0.0005–0.0015, so rounding error is 5–100% per contract. Using Cboe's gamma directly gives +$9.2 bn instead of −$7.7 bn for the base total. That's why gamma is recomputed from IV here; IV is published to 4 decimals of a much larger number.
- **Open interest is as of the previous close.** OI updates once a day, so same-day (0DTE) positioning isn't captured, even though 0–1 day expiries carry large gamma.
- **After the close,** AM-settled SPX contracts expiring the next morning have stopped trading and have no IV. They're included with Cboe's gamma.
- **The flip profile holds IV fixed.** In practice IV rises as spot falls (skew dynamics), which moves the flip.
- **Delay:** the data is 15 minutes delayed and snapshot-only.

## Run it

```bash
pip install -r requirements.txt
python main.py                 # SPX, all expiries, with the sensitivity range (includes SqueezeMetrics)
python main.py --symbol SPY
python main.py --sample        # offline: 90 SPX contracts from one monthly expiry
```

## Files

- `main.py`: entry point
- `requirements.txt`: pinned dependencies
- `sample/chain.csv`: 90 SPX contracts (45 strikes, the 2026-11-20 monthly expiry) with spot and snapshot time

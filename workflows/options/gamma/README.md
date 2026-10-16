# Gamma exposure (GEX): by strike, total, walls, gamma flip and sensitivity range

**Computes:** estimated dealer gamma exposure from an options chain:
- dollar GEX per 1% move, by strike and in total
- the call wall and put wall (strikes with the largest call and put GEX)
- the gamma flip: the spot level where total GEX changes sign, with IVs held fixed
- a sensitivity report: total GEX under five assumptions, with the range, the median and whether the sign is consistent, and for SPX the SqueezeMetrics figure printed beside it as an independent reference

**Inputs:**
- Option `iv`, `gamma` and `open_interest`, plus spot and snapshot time, from [`data-sources/cboe-delayed-quotes.md`](../../../data-sources/cboe-delayed-quotes.md)
- The daily SPX GEX from [`data-sources/squeezemetrics.md`](../../../data-sources/squeezemetrics.md), printed next to the SPX sensitivity range as an independent reference

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

The report gives the **range** (minimum to maximum), the **median** and a **sign verdict**: "consistent" if every estimate has the same sign, "uncertain" if the range crosses zero. The median is the headline estimate because one extreme assumption can't pull it far. The range shows how much the answer depends on choices that can't be observed.

For SPX, SqueezeMetrics' published GEX is printed next to the range as an **independent reference**. It is not part of the median or the verdict: it is a different method with proprietary adjustments, not a different assumption applied to the same inputs, so mixing it in would blur model sensitivity with cross-source disagreement.

## Results on a live snapshot (2026-10-16, 17:39 UTC, midday)

| | SPX | SPY | QQQ |
| --- | --- | --- | --- |
| **Median total GEX (headline)** | **−$86.41 bn** | **−$18.56 bn** | **−$13.18 bn** |
| Range across assumptions | −$91.46 to −$28.10 bn | −$19.00 to −$7.82 bn | −$13.94 to −$6.39 bn |
| Sign verdict | Consistently negative | Consistently negative | Consistently negative |
| Base total GEX (all expiries) | −$91.46 bn | −$19.00 bn | −$13.94 bn |
| Gross call / put GEX | +$207 bn / −$298 bn | +$15 bn / −$34 bn | +$9 bn / −$23 bn |
| Gamma flip | 7,738 (+1.1%) | 773 (+1.4%) | 729 (+2.5%) |
| Base total with Cboe's rounded gamma | −$76.61 bn | −$18.74 bn | −$13.89 bn |
| SqueezeMetrics SPX GEX (2026-10-15), reference only | +$6.02 bn (outside the range) | | |

An after-close snapshot earlier the same day (spot 7,744) gave a base SPX total of −$7.73 bn with a range of −$10.90 to +$8.12 bn across the same five assumptions, so the SPX total moved by tens of billions within one session as spot fell about 1% and 0DTE open interest rolled. Treat any single total as a snapshot, and read the strike-level picture, the walls and the flip level first.

## Caveats

- **Net GEX is a small difference of large numbers.** For SPX it was about 2.5% of gross call or put GEX after the close on 2026-10-16 (and about 18% at midday), so a small change in assumptions can flip its sign. That's why the headline is the median of the sensitivity range, reported with the range and sign verdict, not a single total. When the verdict is "uncertain", don't trade on the sign; the strike-level picture, the walls and the location of the flip are more robust.
- **Dealer positioning is assumed, not observed.** Open interest doesn't say who is long. The "dealers long calls, short puts" rule is a convention and is wrong for, say, overwriting funds that sell calls. That's the main reason the base total doesn't match SqueezeMetrics, whose adjustments are proprietary; their figure is printed beside the SPX range for comparison rather than treated as the right answer.
- **The sensitivity report doesn't vary the positioning assumption.** Every variant keeps dealers long calls and short puts and changes only which expiries count. That assumption is the largest source of uncertainty and open interest can't resolve it, so the range understates the true uncertainty in the sign. Flipping it wholesale just negates the total, which is why no such variant is included; a partial-positioning variant is a candidate for a later revision.
- **Cboe rounds gamma to 4 decimals.** For SPX, near-the-money gammas are around 0.0005–0.0015, so rounding error is 5–100% per contract. In the after-close snapshot on 2026-10-16, using Cboe's gamma directly gave +$9.2 bn instead of −$7.7 bn for the base total; at midday the gap was $15 bn on a $91 bn total. That's why gamma is recomputed from IV here; IV is published to 4 decimals of a much larger number.
- **Open interest is as of the previous close.** OI updates once a day, so same-day (0DTE) positioning isn't captured, even though 0–1 day expiries carry large gamma.
- **After the close,** AM-settled SPX contracts expiring the next morning have stopped trading and have no IV. They're included with Cboe's gamma.
- **The flip profile holds IV fixed.** In practice IV rises as spot falls (skew dynamics), which moves the flip.
- **Delay:** the data is 15 minutes delayed and snapshot-only.

## Run it

```bash
pip install -r requirements.txt
python main.py                 # SPX, all expiries, with the sensitivity range and SqueezeMetrics as a reference
python main.py --symbol SPY
python main.py --sample        # offline: 90 SPX contracts from one monthly expiry
```

## Files

- `main.py`: entry point
- `requirements.txt`: pinned dependencies
- `sample/chain.csv`: 90 SPX contracts (45 strikes, the 2026-11-20 monthly expiry) with spot and snapshot time

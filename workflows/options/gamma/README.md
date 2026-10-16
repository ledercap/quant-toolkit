# Gamma exposure (GEX): by strike, total, walls and gamma flip

**Computes:** estimated dealer gamma exposure from an options chain:
- dollar GEX per 1% move, by strike and in total
- the call wall and put wall (strikes with the largest call and put GEX)
- the gamma flip: the spot level where total GEX changes sign, with IVs held fixed

**Inputs:**
- Option `iv`, `gamma` and `open_interest`, plus spot and snapshot time, from [`data-sources/cboe-delayed-quotes.md`](../../../data-sources/cboe-delayed-quotes.md)
- The daily SPX GEX from [`data-sources/squeezemetrics.md`](../../../data-sources/squeezemetrics.md), as a reference only

**Output:** a printed summary, `output/gex_by_strike_<SYMBOL>.csv` (call, put and net GEX per strike) and `output/gex_profile_<SYMBOL>.csv` (total GEX against hypothetical spot levels from −15% to +15%)

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

## Results on a live snapshot (2026-10-16, after the close)

| | SPX | SPY | QQQ |
| --- | --- | --- | --- |
| Total GEX (per 1% move) | −$7.46 bn | −$8.27 bn | −$9.57 bn |
| Gross call / put GEX | +$302 bn / −$310 bn | +$22 bn / −$30 bn | +$10 bn / −$20 bn |
| Gamma flip | 7,751 (+0.1%) | 776 (+0.5%) | 740 (+2.2%) |
| Same total with Cboe's rounded gamma | +$14.33 bn | −$6.91 bn | −$7.46 bn |
| SqueezeMetrics SPX GEX (2026-10-15) | +$6.02 bn | | |

## Caveats

- **Net GEX is a small difference of large numbers.** For SPX it's about 2% of gross call or put GEX, so a 2–3% change in assumptions can flip its sign. Treat the sign and size as an estimate, not a measurement. The strike-level picture, the walls and the location of the flip are more robust than the headline total.
- **Dealer positioning is assumed, not observed.** Open interest doesn't say who is long. The "dealers long calls, short puts" rule is a convention and is wrong for, say, overwriting funds that sell calls. That's the main reason this doesn't match SqueezeMetrics, whose adjustments are proprietary.
- **Cboe rounds gamma to 4 decimals.** For SPX, near-the-money gammas are around 0.0005–0.0015, so rounding error is 5–100% per contract. Using Cboe's gamma directly gives +$14.3 bn instead of −$7.5 bn. That's why gamma is recomputed from IV here; IV is published to 4 decimals of a much larger number.
- **Open interest is as of the previous close.** OI updates once a day, so same-day (0DTE) positioning isn't captured, even though 0–1 day expiries carry large gamma.
- **After the close,** AM-settled SPX contracts expiring the next morning have stopped trading and have no IV. They're included with Cboe's gamma.
- **The flip profile holds IV fixed.** In practice IV rises as spot falls (skew dynamics), which moves the flip.
- **Delay:** the data is 15 minutes delayed and snapshot-only.

## Run it

```bash
pip install -r requirements.txt
python main.py                 # SPX, all expiries, with the SqueezeMetrics comparison
python main.py --symbol SPY
python main.py --sample        # offline: 90 SPX contracts from one monthly expiry
```

## Files

- `main.py`: entry point
- `requirements.txt`: pinned dependencies
- `sample/chain.csv`: 90 SPX contracts (45 strikes, the 2026-11-20 monthly expiry) with spot and snapshot time

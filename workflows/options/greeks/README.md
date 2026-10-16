# Options Greeks: implied volatility, delta, gamma, vega, theta and rho

**Computes:** for every contract in a Cboe options chain, the implied volatility from the bid/ask mid and the Black-Scholes-Merton Greeks, using a forward price implied from put-call parity and a risk-free rate from the Treasury curve. It then measures how closely the results match the IV and Greeks Cboe publishes.

**Inputs:**
- Option `bid`, `ask`, `iv`, `delta`, `gamma`, `vega` and `theta`, plus spot and snapshot time, from [`data-sources/cboe-delayed-quotes.md`](../../../data-sources/cboe-delayed-quotes.md)
- Daily par yields by tenor from [`data-sources/us-treasury-yield-curve.md`](../../../data-sources/us-treasury-yield-curve.md)

**Output:**
- A per-expiry table (days, rate, forward, implied carry, ATM IV)
- A comparison table against Cboe
- A near-the-money example, and every contract written to `output/greeks_<SYMBOL>.csv`

## Formula

**Time to expiry.** T = (expiry time − snapshot time) / 365 days, in calendar time. SPXW and equity options expire at 16:00 ET. SPX options (root `SPX`) are AM-settled and use 09:30 ET on expiry day.

**Risk-free rate.** Treasury par yields *y* are interpolated linearly by maturity at T, then converted from semiannual bond-equivalent to continuous compounding: r = 2 ln(1 + y/2). (US Treasury, "Treasury Yield Curve Methodology", https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology)

**Forward price** (Cboe Volatility Index Mathematics Methodology, https://cdn.cboe.com/api/global/us_indices/governance/Cboe_Volatility_Index_Mathematics_Methodology.pdf):
1. For each expiry, find the strike K\* where |C − P| (mid prices) is smallest. Ties go to the lowest strike.
2. Then F = K\* + e^{rT} (C − P).
3. The implied carry (dividend yield) is q = r − ln(F/S) / T.

**Implied volatility.** Solve for σ such that the discounted Black (1976) price on the forward equals the mid:

- C = e^{−rT} [F N(d₁) − K N(d₂)]
- P = e^{−rT} [K N(−d₂) − F N(−d₁)]
- d₁ = [ln(F/K) + σ²T/2] / (σ√T)
- d₂ = d₁ − σ√T

The solver uses bisection on σ ∈ [0.001, 5]. Prices at or below intrinsic value, or at or above the no-arbitrage upper bound, get no IV. (Black, F. (1976), "The pricing of commodity contracts", *Journal of Financial Economics* 3, 167–179.)

**Greeks.** Black-Scholes-Merton with continuous dividend yield q:

- d₁ = [ln(S/K) + (r − q + σ²/2)T] / (σ√T)
- d₂ = d₁ − σ√T

| Greek | Call | Put | Units |
| --- | --- | --- | --- |
| Delta | e^{−qT} N(d₁) | e^{−qT} [N(d₁) − 1] | per $1 of spot |
| Gamma | e^{−qT} φ(d₁) / (S σ √T) | same | per $1, per $1 |
| Vega | S e^{−qT} φ(d₁) √T / 100 | same | per 1 vol point |
| Theta | [−S e^{−qT} φ(d₁) σ / (2√T) − rK e^{−rT} N(d₂) + qS e^{−qT} N(d₁)] / 365 | [−S e^{−qT} φ(d₁) σ / (2√T) + rK e^{−rT} N(−d₂) − qS e^{−qT} N(−d₁)] / 365 | per calendar day |
| Theta, decay term only | −S e^{−qT} φ(d₁) σ / (2√T) / 365 | same | per calendar day |
| Rho | K T e^{−rT} N(d₂) / 100 | −K T e^{−rT} N(−d₂) / 100 | per 1 percentage point |

N is the standard normal CDF and φ its density. Sources:
- Black, F. and Scholes, M. (1973), "The Pricing of Options and Corporate Liabilities", *Journal of Political Economy* 81(3), 637–654
- Merton, R. C. (1973), "Theory of Rational Option Pricing", *Bell Journal of Economics and Management Science* 4(1), 141–183
- Hull, J. C., *Options, Futures, and Other Derivatives*, 11th ed. (2021), chapter "The Greek Letters"

## Results on a live snapshot (2026-10-16, after the close)

Median absolute difference from Cboe on liquid contracts (0.10 < |delta| < 0.90, at least 7 days to expiry):

| | SPX (4,852 contracts) | SPY (1,278 contracts) |
| --- | --- | --- |
| IV | 0.009 vol points | 0.24 vol points |
| Delta | 0.0013 | 0.0046 |
| Gamma | 2.0% | 1.3% |
| Vega | 1.2% | 1.9% |
| Theta (decay term) | 0.7% | 2.4% |

## Caveats

- **Cboe's "theta" is the decay term only.** It's identical for a call and put at the same strike and leaves out the rate and dividend carry terms. Compare it with `my_theta_decay`. `my_theta` is the full BSM theta that a P&L actually experiences, and it differs from Cboe's by about 25% near the money.
- **European exercise is assumed.** SPX is European-style. SPY and single stocks are American-style, so early exercise (mostly deep in-the-money puts and calls before dividends) makes BSM slightly off; that's why SPY's differences are larger.
- **Implied carry absorbs stale spot.** Spot in the delayed feed can lag option quotes, especially after the close, so q for expiries under about 3 days can look extreme (for example −19%). Greeks on those expiries are noisy. The 7-day filter in the comparison excludes them.
- **Mid prices:** wide markets give unreliable IVs. Contracts with no bid are dropped, and deep in-the-money and far out-of-the-money quotes are the least reliable.
- **Delay:** the data is 15 minutes delayed and snapshot-only; this isn't a real-time risk system.
- **Rates:** Treasury par yields stand in for the risk-free rate. Market makers typically use SOFR-based rates, a few basis points different. The implied forward absorbs most of the difference.

## Run it

```bash
pip install -r requirements.txt
python main.py                          # SPX, expiries up to 60 days
python main.py --symbol SPY --max-days 30
python main.py --sample                 # offline: 90 SPXW contracts from one expiry
```

## Files

- `main.py`: entry point
- `requirements.txt`: pinned dependencies
- `sample/chain.csv`: 90 SPXW contracts (45 strikes, one expiry about 30 days out) with spot and snapshot time
- `sample/yield_curve.csv`: the Treasury par curve for the same date

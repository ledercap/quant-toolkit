# q (kdb+)

**When to reach for it:** in firms that run kdb+ for market data: banks, HFT and market-making firms, and some hedge funds. q is how you query and analyse tick data there, and how real-time capture is built. Outside that setting, the license and learning curve rarely pay off. Database details are in [databases/kdb.md](../../databases/kdb.md).

## Scores

| Capability | Score | Why |
| --- | --- | --- |
| Data wrangling and cleaning | 4 | Tables and columns are native types, and qSQL plus vector operations reshape time series very concisely. Loses a point for messy text and JSON handling, and for a steep syntax. |
| Financial statement analysis | 2 | Possible but unusual. No fundamentals tooling; data arrives through PyKX or custom loaders. |
| Time series and econometrics | 3 | Superb time-series operations (as-of joins with `aj`, window joins with `wj`, bucketing with `xbar`), but no statistical models built in. |
| Options pricing and Greeks | 3 | Vectorised Black-Scholes is short and fast to write, but there's no pricing library, so complex models are called from C or Python. |
| Backtesting | 3 | Replaying tick data from a historical database is a common in-house pattern, but there are no public frameworks. |
| Low-latency and HFT execution | 3 | The standard tickerplant captures and publishes market data in real time with low latency, but order execution is usually C++ or Java. |
| Numerical computation at scale | 4 | Vector operations over memory-mapped columnar data are extremely fast. Loses a point because the free edition caps memory and threads. |
| Machine learning | 1 | No native ML of note; models run in Python and are called through PyKX or embedPy. |
| Visualisation and reporting | 2 | KX Dashboards and Insights exist (licensed); otherwise data is exported to Python or BI tools. |
| Native fit with data sources | 2 | No clients for the sources here; data comes in via PyKX from Python, or through feed handlers in production. |
| Ecosystem and hiring pool | 2 | A small community and few developers, though experienced q developers are well paid as a result. |

## Libraries and resources

- Docs and tutorials: [code.kx.com](https://code.kx.com), [q for Mortals](https://code.kx.com/q4m3/)
- Python bridge: [PyKX](https://github.com/KxSystems/pykx)
- Licensing and downloads: [kx.com](https://kx.com)

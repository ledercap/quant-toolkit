# Python

**When to reach for it:** the default for research, data work and anything that touches the data sources in this repo. Prototype in Python first, and move only the parts that are too slow into NumPy, Numba, Polars, DuckDB, or a compiled language.

## Scores

| Capability | Score | Why |
| --- | --- | --- |
| Data wrangling and cleaning | 5 | pandas is the lingua franca of financial data, and Polars (written in Rust) adds a fast multi-threaded engine. Both read CSV, JSON, Parquet and SQL directly. |
| Financial statement analysis | 5 | Every fundamentals source here has a Python path, including SEC EDGAR via `requests` or `edgartools`, FMP and Alpha Vantage. pandas handles the tag-and-period reshaping. |
| Time series and econometrics | 4 | `statsmodels` (ARIMA, VAR, cointegration, OLS with robust errors) and `arch` (GARCH, unit-root tests) cover most needs. R is still deeper on specialised econometrics. |
| Options pricing and Greeks | 4 | QuantLib-Python (the full QuantLib engine), `py_vollib` (fast Black-Scholes and implied vol), and vectorised NumPy and SciPy. Pure-Python loops are slow, so vectorise or use Numba. |
| Backtesting | 5 | The widest choice of any language: `vectorbt` (vectorised), `backtrader` and `zipline-reloaded` (event-driven), and NautilusTrader (Python API over a Rust core). |
| Low-latency and HFT execution | 1 | Interpreter overhead, the GIL and garbage-collector pauses make microsecond-level latency impossible. Python sits next to execution (research, signals, monitoring), not in it. |
| Numerical computation at scale | 4 | Pure Python is slow, but NumPy, Numba, JAX and Polars run compiled code underneath, so vectorised work approaches C speed. Loses a point because you have to know which tool to use to avoid slow paths. |
| Machine learning | 5 | scikit-learn, XGBoost and LightGBM, PyTorch and JAX. Every major ML library is Python first. |
| Visualisation and reporting | 4 | matplotlib, Plotly, Altair and seaborn for charts. Jupyter, Streamlit and Quarto for reports and apps. R's ggplot2 is still more consistent for publication-quality statistical charts. |
| Native fit with data sources | 5 | All 16 sources in `data-sources/` have working Python examples. yfinance and ArcticDB are Python only, and Databento's main client is Python. |
| Ecosystem and hiring pool | 5 | The most common language in quant research job postings and the largest open-source finance ecosystem. |

## Libraries

- Data: [pandas](https://pandas.pydata.org), [Polars](https://pola.rs), [NumPy](https://numpy.org), [DuckDB](https://duckdb.org/docs/api/python/overview)
- Econometrics: [statsmodels](https://www.statsmodels.org), [arch](https://github.com/bashtage/arch)
- Pricing: [QuantLib-Python](https://www.quantlib.org), [py_vollib](https://github.com/vollib/py_vollib)
- Backtesting: [vectorbt](https://github.com/polakowo/vectorbt), [backtrader](https://github.com/mementum/backtrader), [zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded), [NautilusTrader](https://github.com/nautechsystems/nautilus_trader)
- Speed: [Numba](https://numba.pydata.org), [JAX](https://github.com/jax-ml/jax)
- ML: [scikit-learn](https://scikit-learn.org), [PyTorch](https://pytorch.org), [XGBoost](https://xgboost.readthedocs.io)
- Charts and reports: [matplotlib](https://matplotlib.org), [Plotly](https://plotly.com/python/), [Streamlit](https://streamlit.io), [Quarto](https://quarto.org)

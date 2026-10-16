# Rust

**When to reach for it:** new trading infrastructure where you want close to C++ speed with memory safety, fast data tooling (Polars itself is Rust), and compiled extensions for Python (via PyO3). Its finance ecosystem is young, so expect to build more yourself.

## Scores

| Capability | Score | Why |
| --- | --- | --- |
| Data wrangling and cleaning | 3 | Polars is native Rust and excellent, but day-to-day wrangling is quicker in Python on top of that same engine. |
| Financial statement analysis | 1 | No fundamentals libraries. You would write the EDGAR client and the reshaping yourself. |
| Time series and econometrics | 2 | A few crates (`linfa` for ML, `statrs`, `augurs` for forecasting), but nothing close to statsmodels or R. |
| Options pricing and Greeks | 2 | Fast enough for any model, and `RustQuant` provides pricers and automatic differentiation, but it is a small project with no production track record next to QuantLib. Expect to write and validate the models yourself. |
| Backtesting | 3 | NautilusTrader's core engine is Rust, which shows it works. Few standalone Rust frameworks. |
| Low-latency and HFT execution | 4 | No garbage collector and zero-cost abstractions give C++-class latency, and the compiler rules out whole classes of memory and concurrency bugs. Adoption at trading firms is growing. One point behind C++ on tooling and the established HFT codebase. |
| Numerical computation at scale | 4 | Native speed, safe multi-threading (Rayon) and SIMD. One point behind C++ and Julia on mature linear algebra and GPU libraries. |
| Machine learning | 2 | `candle` and `burn` exist for inference and some training, but research happens in Python. |
| Visualisation and reporting | 1 | Charting crates (`plotters`) are basic; no reporting ecosystem. |
| Native fit with data sources | 2 | Databento has an official Rust client. Everything else needs `reqwest` and `serde` code you write yourself. |
| Ecosystem and hiring pool | 3 | Growing fast and popular with engineers, but finance-specific libraries and experienced hires are still limited. |

## Libraries

- Data: [Polars](https://pola.rs), [arrow-rs](https://github.com/apache/arrow-rs), [duckdb-rs](https://github.com/duckdb/duckdb-rs)
- Finance: [RustQuant](https://github.com/avhz/RustQuant), [NautilusTrader](https://github.com/nautechsystems/nautilus_trader), [Databento Rust client](https://github.com/databento/databento-rs)
- Numerics: [ndarray](https://github.com/rust-ndarray/ndarray), [nalgebra](https://nalgebra.rs), [Rayon](https://github.com/rayon-rs/rayon)
- Python bindings: [PyO3](https://pyo3.rs), [maturin](https://www.maturin.rs)

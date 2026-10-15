# C++

**When to reach for it:** code in the trading path (market data handlers, order gateways, strategy engines), pricing libraries that other languages call, and performance-critical cores for backtesters or risk engines. Not for exploratory research.

## Scores

| Capability | Score | Why |
| --- | --- | --- |
| Data wrangling and cleaning | 2 | Possible with Apache Arrow C++ or hand-written parsers, but far slower to write and change than Python, R or SQL. |
| Financial statement analysis | 1 | No fundamentals libraries. Reshaping XBRL facts is a poor use of a systems language. |
| Time series and econometrics | 2 | Fast building blocks (Eigen, GSL, Boost) but no econometrics library comparable to statsmodels or R. Models are usually built elsewhere and only the final calculation is ported. |
| Options pricing and Greeks | 5 | QuantLib is written in C++ and is the reference open-source pricing library. Most banks' pricing libraries are C++. Fast Monte Carlo and PDE solvers, and adjoint algorithmic differentiation (AAD) for Greeks. |
| Backtesting | 4 | High-fidelity, event-driven backtesters that replay tick data at full speed are usually C++, often sharing code with the live engine. Loses a point because open-source frameworks are few, so teams build their own. |
| Low-latency and HFT execution | 5 | The industry standard: no garbage collector, control over memory layout and cache use, kernel-bypass networking, and nanosecond-level tuning. See [low-latency-and-hft-execution.md](low-latency-and-hft-execution.md). |
| Numerical computation at scale | 5 | Compiled to native code with SIMD, OpenMP and CUDA. Eigen, Intel oneMKL and BLAS/LAPACK sit under most other languages' numerics. |
| Machine learning | 3 | LibTorch, ONNX Runtime and the XGBoost/LightGBM cores run models fast in production, but models are trained in Python. |
| Visualisation and reporting | 1 | No practical charting or reporting ecosystem; results are exported to other tools. |
| Native fit with data sources | 2 | Databento has a C++ client. Every other source here needs a hand-written HTTP and JSON layer (libcurl plus nlohmann/json). |
| Ecosystem and hiring pool | 4 | Large, mature talent pool and in heavy demand at HFT firms, market makers and banks. Loses a point because experienced low-latency engineers are scarce and expensive. |

## Libraries

- Pricing: [QuantLib](https://www.quantlib.org)
- Numerics: [Eigen](https://eigen.tuxfamily.org), [Boost](https://www.boost.org), [Intel oneMKL](https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl.html)
- Data: [Apache Arrow C++](https://arrow.apache.org/docs/cpp/), [Databento C++ client](https://github.com/databento/databento-cpp)
- ML inference: [LibTorch](https://pytorch.org/cppdocs/), [ONNX Runtime](https://onnxruntime.ai)
- Bindings to Python: [pybind11](https://github.com/pybind/pybind11), [nanobind](https://github.com/wjakob/nanobind)

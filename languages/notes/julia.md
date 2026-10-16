# Julia

**When to reach for it:** heavy numerical models (Monte Carlo pricing, PDE solvers, optimisation, stochastic simulation) where you want readable, high-level code that runs at compiled speed, without the two-language problem of prototyping in Python and rewriting in C++.

## Scores

| Capability | Score | Why |
| --- | --- | --- |
| Data wrangling and cleaning | 4 | DataFrames.jl and DataFramesMeta are capable and fast. Less documentation and fewer examples than pandas or dplyr. |
| Financial statement analysis | 2 | No maintained fundamentals packages; you write the HTTP calls and reshaping yourself. |
| Time series and econometrics | 3 | `StateSpaceModels.jl`, `GLM.jl`, `ARCHModels.jl` and `TimeSeries.jl` exist, but coverage is thinner than in R or Python. |
| Options pricing and Greeks | 4 | Monte Carlo and PDE code runs at C speed, and `ForwardDiff.jl` and `Enzyme.jl` give exact Greeks by automatic differentiation. Loses a point for no QuantLib-sized library (wrappers and smaller packages only). |
| Backtesting | 2 | No widely used backtesting framework. |
| Low-latency and HFT execution | 2 | Fast once compiled, but JIT warm-up and garbage-collector pauses make latency hard to guarantee. |
| Numerical computation at scale | 4 | Designed for this: JIT-compiled to native code, multiple dispatch, native multi-threading and GPU support (CUDA.jl), and the DifferentialEquations.jl and JuMP ecosystems. Loses a point because GPU and distributed tooling trails CUDA C++ and the Python-fronted frameworks (JAX, PyTorch) in maturity and library coverage. |
| Machine learning | 3 | Flux.jl, Lux.jl and MLJ.jl work well, especially scientific ML, but the mainstream is Python. |
| Visualisation and reporting | 3 | Makie and Plots.jl are capable; Pluto notebooks and Quarto support Julia. |
| Native fit with data sources | 2 | Almost no official clients for the sources here; you write HTTP and JSON code yourself (FredData.jl is an exception). |
| Ecosystem and hiring pool | 2 | Used at some asset managers, insurers and energy traders, but the community and job market are small. |

## Libraries

- Data: [DataFrames.jl](https://dataframes.juliadata.org), [DuckDB.jl](https://duckdb.org/docs/api/julia)
- Numerics and AD: [DifferentialEquations.jl](https://docs.sciml.ai/DiffEqDocs/stable/), [ForwardDiff.jl](https://github.com/JuliaDiff/ForwardDiff.jl), [JuMP](https://jump.dev), [CUDA.jl](https://cuda.juliagpu.org)
- Econometrics: [GLM.jl](https://github.com/JuliaStats/GLM.jl), [ARCHModels.jl](https://github.com/s-broda/ARCHModels.jl)
- ML: [Flux.jl](https://fluxml.ai), [MLJ.jl](https://juliaai.github.io/MLJ.jl/)
- Charts: [Makie](https://docs.makie.org), [Pluto.jl](https://plutojl.org)

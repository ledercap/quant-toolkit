# R

**When to reach for it:** econometrics, statistical testing, risk and performance reporting, and publication-quality charts. It is strong where academic finance and statistics overlap, such as GARCH variants, factor models and panel regressions.

## Scores

| Capability | Score | Why |
| --- | --- | --- |
| Data wrangling and cleaning | 5 | `dplyr` and `tidyr` make wrangling readable; `data.table` is among the fastest in-memory engines in any language. `xts` and `zoo` are built for time-indexed financial data. |
| Financial statement analysis | 3 | Workable (`edgarWebR`, `tidyquant`, plain `httr2` plus `jsonlite`), but fewer maintained fundamentals packages than Python. |
| Time series and econometrics | 5 | The deepest ecosystem anywhere: `rugarch`/`rmgarch` (univariate and multivariate GARCH), `vars`, `urca`, `forecast`/`fable`, `plm` for panel data, `sandwich` for robust errors. New methods from the academic literature often appear in R first. |
| Options pricing and Greeks | 3 | `RQuantLib`, `fOptions` and `derivmkts` cover the standard models. Less maintained than QuantLib-Python and slow for large surfaces. |
| Backtesting | 3 | `quantstrat` and `PerformanceAnalytics` (excellent for performance and risk statistics). Development has slowed, and event-driven or intraday backtests are awkward. |
| Low-latency and HFT execution | 1 | Interpreted and single-threaded by default, with no realistic path to execution. |
| Numerical computation at scale | 2 | Vectorised base R is fine for moderate data, but memory use is high and loops are slow. Heavy lifting needs `Rcpp` (C++) or `data.table`/`arrow`. |
| Machine learning | 3 | `tidymodels`, `xgboost`, `ranger` and `torch` for R cover classical ML. Deep learning and newer methods arrive in Python first. |
| Visualisation and reporting | 5 | `ggplot2` is the reference grammar of graphics. R Markdown, Quarto and Shiny produce reports and dashboards straight from analysis code. |
| Native fit with data sources | 3 | Good packages for some sources (`fredr`, `quantmod` and `tidyquant` for FRED and Yahoo, `Rblpapi` for Bloomberg). Most APIs here have no R client, so you write HTTP calls yourself. |
| Ecosystem and hiring pool | 3 | Common in risk, academia, economics and buy-side research. Less common than Python in new quant job postings. |

## Libraries

- Data: [tidyverse](https://www.tidyverse.org), [data.table](https://rdatatable.gitlab.io/data.table/), [xts](https://github.com/joshuaulrich/xts)
- Econometrics: [rugarch](https://cran.r-project.org/package=rugarch), [vars](https://cran.r-project.org/package=vars), [fable](https://fable.tidyverts.org), [plm](https://cran.r-project.org/package=plm)
- Finance: [quantmod](https://www.quantmod.com), [tidyquant](https://business-science.github.io/tidyquant/), [PerformanceAnalytics](https://github.com/braverock/PerformanceAnalytics), [RQuantLib](https://github.com/eddelbuettel/rquantlib)
- Data access: [fredr](https://sboysel.github.io/fredr/), [duckdb](https://duckdb.org/docs/api/r)
- Reporting: [ggplot2](https://ggplot2.tidyverse.org), [Quarto](https://quarto.org), [Shiny](https://shiny.posit.co)

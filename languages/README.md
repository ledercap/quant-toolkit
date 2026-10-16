# Language and capability matrix

Which language for which job. Scores are 1 (weak) to 5 (best in class). Every cell with a score of 4 or 5, or 1 or 2, should have a note in `notes/` explaining why.

| Capability | [Python](notes/python.md) | [R](notes/r.md) | [C++](notes/cpp.md) | [Rust](notes/rust.md) | [Julia](notes/julia.md) | [SQL](notes/sql.md) | [q (kdb+)](notes/q.md) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Data wrangling and cleaning | 5 | 5 | 2 | 3 | 4 | 4 | 4 |
| Financial statement analysis | 5 | 3 | 1 | 1 | 2 | 4 | 2 |
| Time series and econometrics | 4 | 5 | 2 | 2 | 3 | 2 | 3 |
| Options pricing and Greeks | 4 | 3 | 5 | 3 | 4 | 1 | 3 |
| Backtesting | 5 | 3 | 4 | 3 | 2 | 2 | 3 |
| Low-latency and HFT execution | 1 | 1 | 5 | 4 | 2 | 1 | 3 |
| Numerical computation at scale | 4 | 2 | 5 | 4 | 5 | 3 | 4 |
| Machine learning | 5 | 3 | 3 | 2 | 3 | 2 | 1 |
| Visualisation and reporting | 4 | 5 | 1 | 1 | 3 | 2 | 2 |
| Native fit with data sources | 5 | 3 | 2 | 2 | 2 | 3 | 2 |
| Ecosystem and hiring pool | 5 | 3 | 4 | 3 | 2 | 5 | 2 |

The **Other** column is filled with **q (kdb+)**, the vector language built into kdb+ (see [databases/kdb.md](../databases/kdb.md)). It is the most finance-specific language in use. Java, C# and Go also appear in trading infrastructure; they are covered in [notes/low-latency-and-hft-execution.md](notes/low-latency-and-hft-execution.md) and can get their own columns later.

"Native fit with data sources" is scored against the sources in [data-sources/](../data-sources/README.md): whether official clients exist, and how much code it takes to get from an API response to an analysable table.

## Reading the matrix

- **Default for this repo: Python.** It is top or near the top in every research row, and every data source in this repo has a Python example. Workflows are written in Python unless a note says otherwise.
- **Pair Python with SQL** (DuckDB) for storage and set-based queries. The two together cover almost all research work.
- **Reach for R** for econometrics and statistical reporting, **Julia** for heavy numerical models written by one person, **C++ or Rust** when code runs in the trading path or inside a pricing library, and **q** when working in a shop that runs kdb+.

## Notes

Create `notes/<language>.md` for each column with the libraries that justify the scores, links, and when to reach for the language. Create `notes/<capability>.md` where a comparison across languages is more useful than a per-language view.

| Note | Covers |
| --- | --- |
| [python.md](notes/python.md), [r.md](notes/r.md), [cpp.md](notes/cpp.md), [rust.md](notes/rust.md), [julia.md](notes/julia.md), [sql.md](notes/sql.md), [q.md](notes/q.md) | One per column: reasons for each score, libraries, when to use it |
| [low-latency-and-hft-execution.md](notes/low-latency-and-hft-execution.md) | Cross-language comparison for the trading path, including Java, C#, Go and FPGAs |

Scores were set on 2026-10-15 from library documentation and common practice in the industry. They are judgment calls: challenge any of them in a pull request that updates the note with the reason.

# Low-latency and HFT execution

One capability compared across languages. This row matters most for the README's question of "which perform better for higher-frequency trading", and it can't be read off one language's note.

## What "low latency" means here

The time from a market data packet arriving to an order leaving, measured tick to trade. Rough tiers:

| Tier | Tick-to-trade | Typical stack |
| --- | --- | --- |
| Ultra-low latency (HFT market making, arbitrage) | Under 1 microsecond to a few microseconds | FPGA or custom hardware, with C++ for control |
| Low latency (electronic market making, execution algos) | Microseconds to low milliseconds | C++, Rust, or tuned Java |
| Systematic intraday and daily strategies | Milliseconds to seconds and longer | Python or any language; latency rarely matters |

Most strategies researched with this toolkit live in the third tier, so language speed matters far less than data quality and research correctness. Pick the language for research productivity first.

## Comparison

| Language | Score | Why |
| --- | --- | --- |
| C++ | 5 | No garbage collector, full control of memory layout, CPU cache and threads, kernel-bypass networking (Solarflare/AMD Onload, DPDK). The established choice, with the largest existing codebase and the most experienced engineers. |
| Rust | 4 | Same performance class as C++ with memory and thread safety enforced at compile time. Growing use for new systems; less established tooling and fewer veterans than C++. |
| q (kdb+) | 3 | Real-time market data capture (the tickerplant) and analytics at low latency, but order execution is usually handed to C++ or Java. |
| Julia | 2 | Fast compiled code, but JIT warm-up and garbage-collector pauses make worst-case latency unpredictable. |
| Python | 1 | Interpreter overhead, the GIL and garbage collection add milliseconds of jitter. Used for research and orchestration around fast engines (for example NautilusTrader's Python API over a Rust core). |
| R | 1 | Interpreted, single-threaded, not built for event loops. |
| SQL | 1 | A query language, not an execution environment. |

## Not in the matrix (yet)

- **Java:** used widely in low-latency trading (LMAX Disruptor, Chronicle libraries). Garbage-free coding styles and tuned JVMs get it to microsecond latency. Many exchanges and banks run on it.
- **C#:** used for execution and trading front ends at some banks and funds; .NET performance has improved a lot.
- **Go:** good for networked services and infrastructure around trading; garbage collection pauses keep it out of the hottest path.
- **FPGA (Verilog, VHDL, high-level synthesis):** the fastest tier, where feed parsing and order triggers run in hardware in nanoseconds. Specialist hardware and engineering cost.

## Sources

- QuantLib, NautilusTrader and LMAX documentation linked from the per-language notes
- [LMAX Disruptor](https://lmax-exchange.github.io/disruptor/), [Chronicle Software](https://chronicle.software)

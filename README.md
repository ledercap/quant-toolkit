# quant-toolkit

An open-source finance toolkit from [LederCap](https://www.ledercap.com): a building environment for people who work with financial data, code and analysis.

Repo: https://github.com/ledercap/quant-toolkit

## What this is

Most of the work in quantitative finance happens before any model runs: finding the data, choosing the tools, and getting the calculations right. This repo collects that groundwork in one place, organized so that people and agents can find it and build on it.

The goal is to be the best open-source library for builders.

## What's in it

### 1. Data and API library (`data-sources/`)

A reference of open-source and available APIs and datasets for financial data of every kind: filings, financials, options, gamma flows, commodities, futures, oil, and more. Some sources need keys, and that is fine. Each entry says what the source covers, how to access it, and what it costs.

### 2. Language and capability matrix (`languages/`)

Programming languages on one axis, capabilities on the other, with notes and links throughout. It covers when each language is the right choice, which has the best libraries, which perform better for higher-frequency trading, computation and analysis, and how natively each works with the data sources.

### 3. Workflows (`workflows/`)

The calculations themselves, built on the datasets and the language analysis.

- Financial analysis, organized by income statement, balance sheet and cash flow.
- Options and market structure: volume, volatility, gamma and the other Greeks.

Each workflow pairs a short explanation (what it computes, the formula, which data source feeds it) with working code.

### 4. Databases (`databases/`)

How to store and query what the data sources return: which database fits which workload, which language to pair it with, and the schemas and queries that the workflows depend on.

## Roadmap (`sectors/`)

Sector coverage built on the toolkit, starting with space and robotics:

- Market sizing
- The largest players internationally, including the blue-chip tier
- The pick-and-shovel components that go into each
- Analyst coverage on selected companies

This section will change as the work does.

## Repo layout

```
data-sources/   API and dataset reference, one file per source
languages/      Language x capability matrix and notes
workflows/      Calculations, grouped by statement and by options topic
databases/      Storage choices, schemas and queries
sectors/        Sector research built on the toolkit
quanttk/        Shared calculation library the workflows are built on
tests/          Unit and regression tests for quanttk and the workflows
```

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the branch and review flow, and for the templates each section uses.

## License

[MIT](LICENSE).

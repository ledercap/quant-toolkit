# Contributing

This repo is built by people and by coding agents working together. The rules below keep it navigable for both.

## Ground rules

- **Never commit secrets.** API keys go in a local `.env` file (already gitignored). Reference them by name, for example `FRED_API_KEY`, and document them in the source's entry.
- **Never commit raw data.** Link to the source, or include a tiny sample (under 100 rows) that makes an example runnable.
- **Every entry is self-contained.** A reader should be able to open one file and understand what it covers, where the data comes from, and how to run it.
- **Cite sources.** Formulas, definitions and market conventions link to where they came from.
- **Small, focused pull requests.** One data source, one workflow, one matrix row per PR is the right size.

## Branch and review flow

1. Branch from `main`: `git checkout -b <your-name>/<short-topic>`.
2. Commit with a message that says what changed and why.
3. Open a pull request against `main` using the PR template.
4. One review from a maintainer, then squash-merge.

Direct pushes to `main` are for maintainers only.

## Section templates

Each section has a `README.md` describing its layout and a `_TEMPLATE.md` to copy for new entries. Use them.

| Section | Add a... | Copy from |
| --- | --- | --- |
| `data-sources/` | One file per API or dataset | `data-sources/_TEMPLATE.md` |
| `languages/` | A row or column in the matrix, with notes | `languages/README.md` |
| `workflows/` | A folder with `README.md` plus code | `workflows/_TEMPLATE.md` |
| `databases/` | A file per database or storage pattern | `databases/_TEMPLATE.md` |
| `sectors/` | A folder per sector, files per topic | `sectors/README.md` |

## Code conventions

- Python is the default language for workflows. Target Python 3.11 or newer.
- Pin dependencies in the workflow's own `requirements.txt` when it needs anything beyond `pandas` and `numpy`.
- Prefer plain scripts and notebooks that run top to bottom. No hidden state.
- Type hints and docstrings on any function another workflow might import.

## Working with coding agents

If you use Claude Code, Codex, Cursor or similar, the agent reads `CLAUDE.md` at the repo root for the same conventions. Review what it produces before opening a PR. You own the PR, not the agent.

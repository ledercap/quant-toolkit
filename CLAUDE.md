# quant-toolkit: instructions for coding agents

Read `README.md` for what this repo is and `CONTRIBUTING.md` for the rules. Both apply to you.

## Layout

- `data-sources/` one Markdown file per API or dataset, from `_TEMPLATE.md`
- `languages/` the language x capability matrix in `README.md`, notes in `notes/`
- `workflows/` one folder per calculation with a `README.md` and code, from `_TEMPLATE.md`
- `databases/` one file per database or storage pattern, from `_TEMPLATE.md`
- `sectors/` one folder per sector, from `README.md` there

## Rules that matter most

1. Never write an API key, token or password into any file. Use environment variables and name them in the entry.
2. Never commit raw data files larger than a small sample.
3. When you add a data source, fill every field in the template. "Unknown" is an acceptable value. A missing field is not.
4. When you add a workflow, the formula and its source citation go in the README before the code.
5. Keep entries self-contained. Do not create cross-cutting helper modules unless two or more workflows already share the code.
6. Do not restructure sections or rename folders without an issue agreeing to it first.
7. Work on a branch and open a pull request. Do not push to `main`.

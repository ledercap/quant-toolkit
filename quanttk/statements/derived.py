"""Derived line items built from the reported ones, and the combined annual statement table."""

from __future__ import annotations

from datetime import date

import pandas as pd

from quanttk.statements.build import apply_concepts, first_filed
from quanttk.statements.concepts import ALL_CONCEPTS, Concept


def _sum(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Row sum that is NaN only when every component is missing."""
    present = [c for c in cols if c in df]
    return df[present].sum(axis=1, min_count=1) if present else pd.Series(float("nan"), index=df.index)


def add_derived(st: pd.DataFrame) -> pd.DataFrame:
    """Add derived items. Each is documented here and in workflows/financial-analysis/ratios/README.md.

    gross_profit         reported, else revenue - cost_of_revenue
    cost_of_revenue      reported, else revenue - gross_profit
    total_liabilities    reported, else liabilities_and_equity - equity
    total_debt           commercial_paper + short_term_debt + long_term_debt (missing parts count as 0)
    cash_and_investments cash + short_term_investments
    net_debt             total_debt - cash_and_investments
    working_capital      current_assets - current_liabilities
    ebitda               operating_income + depreciation_amortization
    free_cash_flow       operating_cash_flow - capex
    """
    d = st.copy()
    g = lambda c: d[c] if c in d else pd.Series(float("nan"), index=d.index)  # noqa: E731
    d["gross_profit"] = g("gross_profit").fillna(g("revenue") - g("cost_of_revenue"))
    d["cost_of_revenue"] = g("cost_of_revenue").fillna(g("revenue") - g("gross_profit"))
    d["total_liabilities"] = g("total_liabilities").fillna(g("liabilities_and_equity") - g("equity"))
    d["total_debt"] = _sum(d, ["commercial_paper", "short_term_debt", "long_term_debt"])
    d["cash_and_investments"] = _sum(d, ["cash", "short_term_investments"])
    d["net_debt"] = d["total_debt"] - d["cash_and_investments"]
    d["working_capital"] = g("current_assets") - g("current_liabilities")
    d["ebitda"] = g("operating_income") + g("depreciation_amortization")
    d["free_cash_flow"] = g("operating_cash_flow") - g("capex")
    return d


def annual_statements(facts: pd.DataFrame, as_of: date, concepts: dict[str, Concept] | None = None) -> pd.DataFrame:
    """Income statement, balance sheet and cash flow for every fiscal year, point-in-time, plus
    derived items and `first_filed` (the date the year's first 10-K became public).
    Years without revenue are dropped."""
    st = apply_concepts(facts, concepts or ALL_CONCEPTS, as_of)
    st = add_derived(st)
    st["first_filed"] = first_filed(facts, as_of).reindex(st.index)
    return st.dropna(subset=["revenue"]).sort_index()

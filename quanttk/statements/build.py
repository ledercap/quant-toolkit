"""Select annual, point-in-time values from XBRL facts and assemble standardized statements.

Point-in-time rule: only facts filed on or before `as_of` are used, and for each fiscal
year the value from the latest such filing wins. Later 10-Ks re-report prior years, so
restated values replace originals, but only once they were public.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from quanttk.statements.concepts import Concept

ANNUAL_FORMS = {"10-K", "10-K/A"}
ANNUAL_DAYS = (350, 380)


def _prepare(facts: pd.DataFrame, as_of: date) -> pd.DataFrame:
    f = facts.copy()
    if "unit" not in f:  # samples saved before units were recorded hold USD facts only
        f["unit"] = "USD"
    for col in ("start", "end", "filed"):
        f[col] = pd.to_datetime(f[col])
    return f[f["form"].isin(ANNUAL_FORMS) & (f["filed"] <= pd.Timestamp(as_of))]


def _is_annual(f: pd.DataFrame) -> pd.Series:
    days = (f["end"] - f["start"]).dt.days
    return days.between(*ANNUAL_DAYS)


def fiscal_year_ends(facts: pd.DataFrame, as_of: date) -> pd.DatetimeIndex:
    """Fiscal year-end dates: the end dates of annual duration facts filed by as_of."""
    f = _prepare(facts, as_of)
    return pd.DatetimeIndex(sorted(f.loc[_is_annual(f), "end"].unique()))


def annual_duration_values(facts: pd.DataFrame, as_of: date, unit: str = "USD") -> pd.DataFrame:
    """Wide table (fiscal year end x tag) of annual amounts from 10-K forms, latest filing on or before as_of."""
    f = _prepare(facts, as_of)
    f = f[_is_annual(f) & (f["unit"] == unit)]
    f = f.sort_values("filed").groupby(["tag", "end"], as_index=False).last()
    return f.pivot(index="end", columns="tag", values="value")


def annual_instant_values(facts: pd.DataFrame, as_of: date, unit: str = "USD") -> pd.DataFrame:
    """Wide table (fiscal year end x tag) of balances on fiscal year-end dates, latest filing on or before as_of."""
    f = _prepare(facts, as_of)
    year_ends = fiscal_year_ends(facts, as_of)
    f = f[f["start"].isna() & (f["unit"] == unit) & f["end"].isin(year_ends)]
    f = f.sort_values("filed").groupby(["tag", "end"], as_index=False).last()
    return f.pivot(index="end", columns="tag", values="value")


def first_filed(facts: pd.DataFrame, as_of: date) -> pd.Series:
    """For each fiscal year end, the date the first 10-K reporting it was filed (when it became public)."""
    f = _prepare(facts, as_of)
    f = f[_is_annual(f)]
    return f.groupby("end")["filed"].min()


def apply_concepts(facts: pd.DataFrame, concepts: dict[str, Concept], as_of: date) -> pd.DataFrame:
    """Line items (columns) by fiscal year end (rows), using each concept's tag priority, kind and unit."""
    tables: dict[tuple[str, str], pd.DataFrame] = {}
    out: dict[str, pd.Series] = {}
    for item, concept in concepts.items():
        key = (concept.kind, concept.unit)
        if key not in tables:
            builder = annual_duration_values if concept.kind == "duration" else annual_instant_values
            tables[key] = builder(facts, as_of, unit=concept.unit)
        wide = tables[key]
        series = pd.Series(np.nan, index=wide.index, dtype=float)
        for tag in concept.tags:  # earlier tags win; later tags only fill years still missing
            if tag in wide:
                series = series.fillna(wide[tag])
        out[item] = series
    if not out:
        return pd.DataFrame()
    index = sorted(set().union(*(s.index for s in out.values())))
    return pd.DataFrame({k: v.reindex(index) for k, v in out.items()}, index=pd.DatetimeIndex(index, name="end"))


def coverage_warnings(st: pd.DataFrame, items: list[str]) -> list[str]:
    """Flag line items reported in an earlier year but missing in a later one.

    SEC company facts only include standard us-gaap tags, so when a filer moves a line to a
    company-specific tag the item silently disappears. Derived items treat missing parts as 0
    (e.g. cash_and_investments), so a gap like this understates them. Better to say so.
    """
    warnings = []
    for item in items:
        if item not in st:
            continue
        s = st[item]
        reported = s.notna()
        for end in s.index[(~reported) & reported.cummax()]:
            warnings.append(f"{item} is missing for the year ending {end.date()} but was reported earlier: "
                            "either the balance is now zero or not disclosed, or the filer moved it to a "
                            "company-specific XBRL tag; check the 10-K")
    return warnings


def consecutive_years(index: pd.Index) -> pd.Series:
    """True where a row's fiscal year end is about one year after the previous row's."""
    return index.to_series().diff().dt.days.between(*ANNUAL_DAYS)


def growth(series: pd.Series, positive_base: bool = False) -> pd.Series:
    """Year-over-year growth X_t / X_{t-1} - 1, only between consecutive fiscal years.

    With positive_base=True, growth is NaN when the prior year is zero or negative: growth
    from a loss (e.g. free cash flow going from -17bn to +32bn) has no meaningful percentage.
    """
    prior = series.shift(1)
    g = (series / prior - 1).where(consecutive_years(series.index))
    return g.where(prior > 0) if positive_base else g


def average_balance(series: pd.Series) -> pd.Series:
    """Average of opening and closing balance, (X_{t-1} + X_t) / 2, for ratios that mix a
    period amount with a balance (ROE, asset turnover). NaN where the prior year is missing."""
    return ((series + series.shift(1)) / 2).where(consecutive_years(series.index))

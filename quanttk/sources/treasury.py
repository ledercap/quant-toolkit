"""US Treasury daily par yield curve. See data-sources/us-treasury-yield-curve.md."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

TREASURY_CSV = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
)


def load_yield_curve(on: date) -> pd.Series:
    """Latest published par yield curve on or before `on`, as decimal yields indexed by tenor in years."""
    for year in (on.year, on.year - 1):  # early January may have no rows yet for the new year
        curve = pd.read_csv(TREASURY_CSV.format(year=year), parse_dates=["Date"])
        curve = curve[curve["Date"].dt.date <= on]
        if not curve.empty:
            break
    row = curve.sort_values("Date").iloc[-1].drop("Date").dropna()
    years = [float(c.split()[0]) / (12 if ("Mo" in c or "Month" in c) else 1) for c in row.index]
    return pd.Series(row.values.astype(float) / 100, index=years).sort_index()


def load_sample_curve(path) -> pd.Series:
    """Read a saved curve with columns tenor_years, yield (decimal)."""
    df = pd.read_csv(path)
    return pd.Series(df["yield"].values, index=df["tenor_years"].values)


def continuous_rate(curve: pd.Series, T: np.ndarray) -> np.ndarray:
    """Interpolate par yields linearly in maturity, then convert from semiannual bond-equivalent
    to continuous compounding: r = 2 ln(1 + y/2). Flat beyond the shortest and longest tenors."""
    y = np.interp(T, curve.index.values, curve.values)
    return 2 * np.log1p(y / 2)

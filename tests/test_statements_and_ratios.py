"""Point-in-time statement selection, tag priority, derived items and the ratio identities."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from quanttk.ratios import RATIOS, compute_ratios
from quanttk.statements.build import annual_instant_values, apply_concepts, average_balance, growth
from quanttk.statements.concepts import ALL_CONCEPTS
from quanttk.statements.derived import add_derived, annual_statements


def fact(tag, end, value, filed, start=None, form="10-K", unit="USD"):
    return {"tag": tag, "unit": unit, "start": start, "end": end, "value": value, "form": form, "filed": filed}


FACTS = pd.DataFrame([
    # FY2023 revenue, originally 100, restated to 110 in the FY2024 10-K
    fact("Revenues", "2023-12-31", 100, "2024-02-15", start="2023-01-01"),
    fact("Revenues", "2023-12-31", 110, "2025-02-15", start="2023-01-01"),
    fact("Revenues", "2024-12-31", 130, "2025-02-15", start="2024-01-01"),
    # a newer tag reported only for FY2024 takes priority over Revenues
    fact("RevenueFromContractWithCustomerExcludingAssessedTax", "2024-12-31", 131, "2025-02-15", start="2024-01-01"),
    # a quarterly fact (not annual) must be ignored
    fact("Revenues", "2024-03-31", 30, "2024-05-01", start="2024-01-01", form="10-Q"),
    # balance sheet: assets at year ends, plus a mid-year instant that is not a year end
    fact("Assets", "2023-12-31", 500, "2024-02-15"),
    fact("Assets", "2024-12-31", 600, "2025-02-15"),
    fact("Assets", "2024-06-30", 999, "2025-02-15"),
])
REV = {"revenue": ALL_CONCEPTS["revenue"]}


def test_point_in_time_uses_only_what_was_filed():
    early = apply_concepts(FACTS, REV, date(2024, 6, 30))
    late = apply_concepts(FACTS, REV, date(2025, 6, 30))
    assert early["revenue"].to_dict() == {pd.Timestamp("2023-12-31"): 100}
    assert late.loc["2023-12-31", "revenue"] == 110          # restated value once public
    assert late.loc["2024-12-31", "revenue"] == 131          # priority tag wins


def test_instant_values_only_on_fiscal_year_ends():
    wide = annual_instant_values(FACTS, date(2025, 6, 30))
    assert list(wide.index) == [pd.Timestamp("2023-12-31"), pd.Timestamp("2024-12-31")]
    assert wide["Assets"].tolist() == [500, 600]


def test_growth_and_average_need_consecutive_years():
    s = pd.Series([100.0, 110.0, 121.0], index=pd.to_datetime(["2021-12-31", "2022-12-31", "2024-12-31"]))
    assert growth(s).tolist()[1] == pytest.approx(0.10)
    assert np.isnan(growth(s).iloc[2])                      # 2023 missing: no growth across a gap
    assert average_balance(s).iloc[1] == pytest.approx(105.0)
    assert np.isnan(average_balance(s).iloc[2])


def _statements():
    idx = pd.to_datetime(["2023-12-31", "2024-12-31"])
    st = pd.DataFrame({
        "revenue": [1000.0, 1200.0], "cost_of_revenue": [600.0, 700.0], "operating_income": [200.0, 260.0],
        "net_income": [150.0, 180.0], "total_assets": [2000.0, 2400.0], "equity": [800.0, 1000.0],
        "current_assets": [500.0, 600.0], "current_liabilities": [400.0, 450.0], "cash": [100.0, 150.0],
        "short_term_investments": [50.0, np.nan], "receivables": [120.0, 140.0], "inventory": [80.0, 90.0],
        "payables": [90.0, 100.0], "long_term_debt": [300.0, 280.0], "operating_cash_flow": [220.0, 250.0],
        "capex": [50.0, 60.0], "depreciation_amortization": [40.0, 45.0], "pretax_income": [190.0, 230.0],
        "income_tax": [40.0, 50.0],
    }, index=idx)
    return add_derived(st)


def test_derived_items():
    d = _statements()
    assert d["gross_profit"].tolist() == [400.0, 500.0]
    assert d["total_debt"].tolist() == [300.0, 280.0]                    # missing debt parts count as zero
    assert d["cash_and_investments"].tolist() == [150.0, 150.0]          # missing STI counts as zero
    assert d["free_cash_flow"].tolist() == [170.0, 190.0]
    assert d["ebitda"].tolist() == [240.0, 305.0]


def test_dupont_identity_holds():
    r = compute_ratios(_statements()).iloc[-1]
    assert r["dupont_net_margin"] * r["dupont_asset_turnover"] * r["dupont_equity_multiplier"] == pytest.approx(r["roe"])


def test_known_ratio_values():
    r = compute_ratios(_statements()).iloc[-1]
    assert r["roe"] == pytest.approx(180 / 900)                          # average equity
    assert r["current_ratio"] == pytest.approx(600 / 450)
    assert r["cash_conversion_cycle"] == pytest.approx((130 / 1200 + 85 / 700 - 95 / 700) * 365)
    assert r["revenue_growth"] == pytest.approx(0.2)


def test_ratios_never_raise_on_zero_or_missing():
    d = _statements()
    d["current_liabilities"] = 0.0
    r = compute_ratios(d)
    assert r["current_ratio"].isna().all()
    assert np.isfinite(r.select_dtypes("number").fillna(0).values).all()


def test_registry_names_unique_and_documented():
    names = [r.name for r in RATIOS]
    assert len(names) == len(set(names))
    assert all(r.formula and r.source and r.category for r in RATIOS)


def test_annual_statements_runs_on_sparse_facts():
    st = annual_statements(FACTS, date(2025, 6, 30))
    assert st.loc["2024-12-31", "revenue"] == 131
    assert st.loc["2024-12-31", "total_assets"] == 600

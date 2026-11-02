"""Ratio registry. Each ratio has a category, a formula string, its inputs and a source.

Conventions:
- Ratios that mix a period amount with a balance (ROA, ROE, ROIC, turnover, days ratios)
  divide by the AVERAGE of opening and closing balances, (X_{t-1} + X_t) / 2, so they need
  the prior year and are NaN for the first year shown.
- Division by zero or by a missing value gives NaN, never an error or infinity.
- Growth of items that can be negative (operating income, EPS, free cash flow) is NaN when
  the prior year is zero or negative, since growth from a loss has no meaningful percentage.
- Valuation ratios use the as-traded price on the date the year's first 10-K was filed
  (`first_filed`), so a backtest never sees a ratio before the filing was public.

Sources (keys used in SOURCE below):
  CFA   CFA Institute, International Financial Statement Analysis, 4th ed. (2020),
        "Financial Analysis Techniques" (common ratios, DuPont, cash conversion cycle)
  KGW   Koller, Goedhart and Wessels, Valuation: Measuring and Managing the Value of
        Companies, 7th ed. (2020), McKinsey & Company (NOPAT, invested capital, ROIC)
  HC    Hribar, P. and Collins, D. (2002), "Errors in Estimating Accruals", Journal of
        Accounting Research 40(1), 105-134 (cash-flow accruals); Sloan, R. (1996),
        The Accounting Review 71(3), 289-315 (accruals and earnings quality)
  DAM   Damodaran, A., Investment Valuation, 3rd ed. (2012), Wiley (multiples, EV)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from quanttk.statements.build import average_balance, growth

DEFAULT_TAX_RATE = 0.21  # US federal statutory rate, used when the effective rate is unusable


def div(a: pd.Series, b: pd.Series) -> pd.Series:
    """a / b with NaN where b is zero or missing."""
    return a / b.replace(0, np.nan)


def col(d: pd.DataFrame, name: str) -> pd.Series:
    return d[name] if name in d else pd.Series(np.nan, index=d.index)


def effective_tax_rate(d: pd.DataFrame) -> pd.Series:
    """income_tax / pretax_income, kept only inside [0%, 50%]; otherwise the 21% default."""
    rate = div(col(d, "income_tax"), col(d, "pretax_income"))
    return rate.where(rate.between(0, 0.5), DEFAULT_TAX_RATE)


def nopat(d: pd.DataFrame) -> pd.Series:
    return col(d, "operating_income") * (1 - effective_tax_rate(d))


def invested_capital(d: pd.DataFrame) -> pd.Series:
    """Financing view: total debt + equity - cash and short-term investments (KGW)."""
    return col(d, "total_debt") + col(d, "equity") - col(d, "cash_and_investments").fillna(0)


@dataclass(frozen=True)
class Ratio:
    name: str
    category: str
    formula: str
    compute: Callable[[pd.DataFrame], pd.Series]
    source: str
    unit: str = "x"  # "%", "x" (times) or "days"


A = average_balance
RATIOS: list[Ratio] = [
    # Profitability
    Ratio("gross_margin", "profitability", "gross_profit / revenue", lambda d: div(d.gross_profit, d.revenue), "CFA", "%"),
    Ratio("operating_margin", "profitability", "operating_income / revenue", lambda d: div(d.operating_income, d.revenue), "CFA", "%"),
    Ratio("ebitda_margin", "profitability", "ebitda / revenue", lambda d: div(d.ebitda, d.revenue), "CFA", "%"),
    Ratio("net_margin", "profitability", "net_income / revenue", lambda d: div(d.net_income, d.revenue), "CFA", "%"),
    Ratio("roa", "profitability", "net_income / avg(total_assets)", lambda d: div(d.net_income, A(d.total_assets)), "CFA", "%"),
    Ratio("roe", "profitability", "net_income / avg(equity)", lambda d: div(d.net_income, A(d.equity)), "CFA", "%"),
    Ratio("roic", "profitability", "operating_income x (1 - tax rate) / avg(total_debt + equity - cash_and_investments)",
          lambda d: div(nopat(d), A(invested_capital(d))), "KGW", "%"),
    # DuPont: roe = net margin x asset turnover x equity multiplier (all on average balances)
    Ratio("dupont_net_margin", "dupont", "net_income / revenue", lambda d: div(d.net_income, d.revenue), "CFA", "%"),
    Ratio("dupont_asset_turnover", "dupont", "revenue / avg(total_assets)", lambda d: div(d.revenue, A(d.total_assets)), "CFA"),
    Ratio("dupont_equity_multiplier", "dupont", "avg(total_assets) / avg(equity)", lambda d: div(A(d.total_assets), A(d.equity)), "CFA"),
    # Liquidity
    Ratio("current_ratio", "liquidity", "current_assets / current_liabilities", lambda d: div(d.current_assets, d.current_liabilities), "CFA"),
    Ratio("quick_ratio", "liquidity", "(cash_and_investments + receivables) / current_liabilities",
          lambda d: div(d.cash_and_investments + col(d, "receivables").fillna(0), d.current_liabilities), "CFA"),
    Ratio("cash_ratio", "liquidity", "cash_and_investments / current_liabilities", lambda d: div(d.cash_and_investments, d.current_liabilities), "CFA"),
    # Leverage and solvency
    Ratio("debt_to_equity", "leverage", "total_debt / equity", lambda d: div(d.total_debt, d.equity), "CFA"),
    Ratio("debt_to_assets", "leverage", "total_debt / total_assets", lambda d: div(d.total_debt, d.total_assets), "CFA"),
    Ratio("liabilities_to_assets", "leverage", "total_liabilities / total_assets", lambda d: div(d.total_liabilities, d.total_assets), "CFA"),
    Ratio("equity_multiplier", "leverage", "total_assets / equity", lambda d: div(d.total_assets, d.equity), "CFA"),
    Ratio("net_debt_to_ebitda", "leverage", "net_debt / ebitda", lambda d: div(d.net_debt, d.ebitda), "DAM"),
    Ratio("interest_coverage", "leverage", "operating_income / interest_expense", lambda d: div(d.operating_income, col(d, "interest_expense")), "CFA"),
    # Efficiency
    Ratio("asset_turnover", "efficiency", "revenue / avg(total_assets)", lambda d: div(d.revenue, A(d.total_assets)), "CFA"),
    Ratio("dso", "efficiency", "avg(receivables) / revenue x 365", lambda d: div(A(col(d, "receivables")), d.revenue) * 365, "CFA", "days"),
    Ratio("dio", "efficiency", "avg(inventory) / cost_of_revenue x 365", lambda d: div(A(col(d, "inventory")), d.cost_of_revenue) * 365, "CFA", "days"),
    Ratio("dpo", "efficiency", "avg(payables) / cost_of_revenue x 365", lambda d: div(A(col(d, "payables")), d.cost_of_revenue) * 365, "CFA", "days"),
    Ratio("cash_conversion_cycle", "efficiency", "dso + dio - dpo",
          lambda d: (div(A(col(d, "receivables")), d.revenue) + div(A(col(d, "inventory")), d.cost_of_revenue)
                     - div(A(col(d, "payables")), d.cost_of_revenue)) * 365, "CFA", "days"),
    # Cash flow quality
    Ratio("fcf_margin", "cash_quality", "free_cash_flow / revenue", lambda d: div(d.free_cash_flow, d.revenue), "CFA", "%"),
    Ratio("fcf_conversion", "cash_quality", "free_cash_flow / net_income", lambda d: div(d.free_cash_flow, d.net_income), "CFA"),
    Ratio("accruals_ratio", "cash_quality", "(net_income - operating_cash_flow) / avg(total_assets)",
          lambda d: div(d.net_income - d.operating_cash_flow, A(d.total_assets)), "HC", "%"),
    Ratio("capex_intensity", "cash_quality", "capex / revenue", lambda d: div(d.capex, d.revenue), "CFA", "%"),
    Ratio("capex_to_depreciation", "cash_quality", "capex / depreciation_amortization", lambda d: div(d.capex, col(d, "depreciation_amortization")), "CFA"),
    Ratio("payout_ratio", "cash_quality", "dividends_paid / net_income", lambda d: div(col(d, "dividends_paid"), d.net_income), "CFA", "%"),
    Ratio("total_payout_ratio", "cash_quality", "(dividends_paid + buybacks) / net_income",
          lambda d: div(col(d, "dividends_paid").fillna(0) + col(d, "buybacks").fillna(0), d.net_income), "CFA", "%"),
    # Growth (consecutive fiscal years only)
    Ratio("revenue_growth", "growth", "revenue_t / revenue_{t-1} - 1", lambda d: growth(d.revenue), "CFA", "%"),
    Ratio("operating_income_growth", "growth", "operating_income_t / operating_income_{t-1} - 1", lambda d: growth(d.operating_income, positive_base=True), "CFA", "%"),
    Ratio("eps_growth", "growth", "eps_diluted_t / eps_diluted_{t-1} - 1", lambda d: growth(col(d, "eps_diluted"), positive_base=True), "CFA", "%"),
    Ratio("fcf_growth", "growth", "free_cash_flow_t / free_cash_flow_{t-1} - 1", lambda d: growth(d.free_cash_flow, positive_base=True), "CFA", "%"),
    # Valuation (needs price and market_cap columns; see add_valuation_inputs)
    Ratio("pe", "valuation", "price / eps_diluted", lambda d: div(col(d, "price"), col(d, "eps_diluted")), "DAM"),
    Ratio("pb", "valuation", "market_cap / equity", lambda d: div(col(d, "market_cap"), d.equity), "DAM"),
    Ratio("ev_to_sales", "valuation", "enterprise_value / revenue", lambda d: div(col(d, "enterprise_value"), d.revenue), "DAM"),
    Ratio("ev_to_ebitda", "valuation", "enterprise_value / ebitda", lambda d: div(col(d, "enterprise_value"), d.ebitda), "DAM"),
    Ratio("earnings_yield", "valuation", "net_income / market_cap", lambda d: div(d.net_income, col(d, "market_cap")), "DAM", "%"),
    Ratio("fcf_yield", "valuation", "free_cash_flow / market_cap", lambda d: div(d.free_cash_flow, col(d, "market_cap")), "DAM", "%"),
]
RATIOS_BY_NAME = {r.name: r for r in RATIOS}


def add_valuation_inputs(st: pd.DataFrame, closes: pd.Series) -> pd.DataFrame:
    """Add price (as-traded close on or before first_filed), market_cap (price x shares_outstanding)
    and enterprise_value (market_cap + net_debt)."""
    from quanttk.sources.prices import price_on_or_before

    d = st.copy()
    d["price"] = [price_on_or_before(closes, f) if pd.notna(f) else np.nan for f in d["first_filed"]]
    d["market_cap"] = d["price"] * col(d, "shares_outstanding")
    d["enterprise_value"] = d["market_cap"] + d["net_debt"]
    return d


def compute_ratios(st: pd.DataFrame, categories: list[str] | None = None) -> pd.DataFrame:
    """Every registered ratio (columns) for every fiscal year (rows)."""
    chosen = [r for r in RATIOS if categories is None or r.category in categories]
    return pd.DataFrame({r.name: r.compute(st) for r in chosen}, index=st.index)


def ratio_table() -> pd.DataFrame:
    """The registry as a table (for documentation and the --list option)."""
    return pd.DataFrame([{"ratio": r.name, "category": r.category, "unit": r.unit, "formula": r.formula, "source": r.source}
                         for r in RATIOS])

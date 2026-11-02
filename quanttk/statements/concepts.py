"""Line items and the us-gaap XBRL tags that report them, in priority order.

Companies switch tags over time (Apple used `Revenues` until FY2018, then
`RevenueFromContractWithCustomerExcludingAssessedTax`), so each line item lists several
tags: the first tag with a value for a year wins, later tags only fill years still missing.

`kind` is "duration" for amounts over the fiscal year (income statement, cash flow) and
"instant" for balances on the fiscal year-end date (balance sheet).
Tag definitions: FASB US GAAP Financial Reporting Taxonomy, https://xbrl.fasb.org
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Concept:
    tags: tuple[str, ...]
    kind: str = "duration"  # "duration" or "instant"
    unit: str = "USD"


INCOME_STATEMENT: dict[str, Concept] = {
    "revenue": Concept(("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet",
                        "RevenueFromContractWithCustomerIncludingAssessedTax")),
    "cost_of_revenue": Concept(("CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold")),
    "gross_profit": Concept(("GrossProfit",)),
    "operating_income": Concept(("OperatingIncomeLoss",)),
    "net_income": Concept(("NetIncomeLoss",)),
    "interest_expense": Concept(("InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt")),
    "pretax_income": Concept(("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                              "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments")),
    "income_tax": Concept(("IncomeTaxExpenseBenefit",)),
    "eps_diluted": Concept(("EarningsPerShareDiluted",), unit="USD/shares"),
    "diluted_shares": Concept(("WeightedAverageNumberOfDilutedSharesOutstanding",), unit="shares"),
}

BALANCE_SHEET: dict[str, Concept] = {
    "cash": Concept(("CashAndCashEquivalentsAtCarryingValue",
                     "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"), kind="instant"),
    "short_term_investments": Concept(("MarketableSecuritiesCurrent", "ShortTermInvestments",
                                       "AvailableForSaleSecuritiesDebtSecuritiesCurrent"), kind="instant"),
    "receivables": Concept(("AccountsReceivableNetCurrent", "ReceivablesNetCurrent"), kind="instant"),
    "inventory": Concept(("InventoryNet",), kind="instant"),
    "current_assets": Concept(("AssetsCurrent",), kind="instant"),
    "total_assets": Concept(("Assets",), kind="instant"),
    "payables": Concept(("AccountsPayableCurrent",), kind="instant"),
    "current_liabilities": Concept(("LiabilitiesCurrent",), kind="instant"),
    "commercial_paper": Concept(("CommercialPaper",), kind="instant"),
    "short_term_debt": Concept(("DebtCurrent", "LongTermDebtCurrent", "ShortTermBorrowings"), kind="instant"),
    "long_term_debt": Concept(("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"), kind="instant"),
    "total_liabilities": Concept(("Liabilities",), kind="instant"),
    "equity": Concept(("StockholdersEquity",
                       "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"), kind="instant"),
    "liabilities_and_equity": Concept(("LiabilitiesAndStockholdersEquity",), kind="instant"),
    "shares_outstanding": Concept(("CommonStockSharesOutstanding",), kind="instant", unit="shares"),
}

CASH_FLOW: dict[str, Concept] = {
    "operating_cash_flow": Concept(("NetCashProvidedByUsedInOperatingActivities",
                                    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations")),
    "capex": Concept(("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets")),
    "depreciation_amortization": Concept(("DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
                                          "DepreciationAmortizationAndAccretionNet", "Depreciation")),
    "stock_based_compensation": Concept(("ShareBasedCompensation", "AllocatedShareBasedCompensationExpense")),
    "dividends_paid": Concept(("PaymentsOfDividends", "PaymentsOfDividendsCommonStock")),
    "buybacks": Concept(("PaymentsForRepurchaseOfCommonStock",)),
    "investing_cash_flow": Concept(("NetCashProvidedByUsedInInvestingActivities",
                                    "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations")),
    "financing_cash_flow": Concept(("NetCashProvidedByUsedInFinancingActivities",
                                    "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations")),
}

ALL_CONCEPTS: dict[str, Concept] = {**INCOME_STATEMENT, **BALANCE_SHEET, **CASH_FLOW}


def tags_for(concepts: dict[str, Concept]) -> set[str]:
    """Every XBRL tag needed to build these line items."""
    return {t for c in concepts.values() for t in c.tags}

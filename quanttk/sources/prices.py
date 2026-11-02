"""Daily closing prices. See data-sources/yfinance.md (and data-sources/massive.md for a licensed upgrade).

yfinance is free but unofficial and licensed for personal use only. Every caller goes
through `daily_closes`, so switching to a licensed source later changes one function.
Requires yfinance (pip install yfinance).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

# Cboe symbols -> Yahoo symbols for the underlying index
YAHOO_SYMBOLS = {"_SPX": "^GSPC", "SPX": "^GSPC", "_VIX": "^VIX", "_NDX": "^NDX", "_RUT": "^RUT"}


def daily_closes(ticker: str, start: date, end: date | None = None, adjusted: bool = False) -> pd.Series:
    """Daily closes indexed by date. `adjusted=False` returns as-traded prices (what a valuation
    ratio on a filing date should use); `adjusted=True` gives split- and dividend-adjusted closes
    (what return and volatility calculations should use)."""
    import yfinance as yf

    symbol = YAHOO_SYMBOLS.get(ticker, ticker).replace(".", "-")
    data = yf.download(symbol, start=start, end=end, auto_adjust=adjusted, progress=False)
    if data.empty:
        raise ValueError(f"no prices returned for {symbol}")
    close = data["Close"]
    if isinstance(close, pd.DataFrame):  # newer yfinance returns a column per ticker
        close = close.iloc[:, 0]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.dropna().rename(symbol)


def price_on_or_before(closes: pd.Series, when) -> float:
    """Last close on or before `when` (NaN if none): the price known on that date."""
    s = closes[closes.index <= pd.Timestamp(when)]
    return float(s.iloc[-1]) if len(s) else float("nan")

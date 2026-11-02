"""Cboe delayed option and index quotes. See data-sources/cboe-delayed-quotes.md."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from quanttk.sources.http import get_json

ET = ZoneInfo("America/New_York")
SECONDS_PER_YEAR = 365.0 * 24 * 3600
OPTIONS_URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
QUOTE_URL = "https://cdn.cboe.com/api/global/delayed_quotes/quotes/{symbol}.json"
# SPX (not SPXW) options are AM-settled: they stop trading the day before and settle at
# the open of expiry day. Everything else in Cboe's feed is treated as PM-settled (16:00 ET).
AM_SETTLED_ROOTS = {"SPX"}
OCC_PATTERN = r"^(?P<root>[A-Z]+)(?P<ymd>\d{6})(?P<cp>[CP])(?P<k>\d{8})$"


def load_chain(symbol: str) -> tuple[pd.DataFrame, float, pd.Timestamp]:
    """Cboe delayed chain -> (contracts, spot, snapshot time in UTC).

    Indexes take an underscore prefix (_SPX, _VIX); Cboe's `timestamp` field is UTC.
    """
    raw = get_json(OPTIONS_URL.format(symbol=symbol))
    chain = pd.DataFrame(raw["data"]["options"])
    return chain, float(raw["data"]["current_price"]), pd.Timestamp(raw["timestamp"], tz="UTC")


def load_quote(symbol: str) -> dict:
    """Delayed quote for an index or stock (e.g. _VIX, _SPX, SPY): price, close, timestamp."""
    raw = get_json(QUOTE_URL.format(symbol=symbol))
    return {**raw["data"], "timestamp_utc": pd.Timestamp(raw["timestamp"], tz="UTC")}


def parse_contracts(chain: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """Split OCC symbols (e.g. SPXW261120C07700000) and add strike, expiry, time to expiry and mid.

    Adds: root, ymd, cp, k, strike, expiry (date), expiry_utc, T (years, calendar time,
    ACT/365 to the settlement time) and mid ((bid + ask) / 2).
    """
    parts = chain["option"].str.extract(OCC_PATTERN)
    df = chain.join(parts)
    df["strike"] = df["k"].astype(int) / 1000
    expiry_day = pd.to_datetime(df["ymd"], format="%y%m%d")
    settle_hour = np.where(df["root"].isin(AM_SETTLED_ROOTS), 9.5, 16.0)
    expiry_et = expiry_day + pd.to_timedelta(settle_hour, unit="h")
    df["expiry"] = expiry_day.dt.date
    df["expiry_utc"] = expiry_et.dt.tz_localize(ET).dt.tz_convert("UTC")
    df["T"] = (df["expiry_utc"] - snapshot).dt.total_seconds() / SECONDS_PER_YEAR
    df["mid"] = (df["bid"] + df["ask"]) / 2
    return df


def load_sample_chain(path) -> tuple[pd.DataFrame, float, pd.Timestamp]:
    """Read a saved sample chain (Cboe columns plus `spot` and `snapshot_utc`)."""
    chain = pd.read_csv(path)
    return chain, float(chain["spot"].iloc[0]), pd.Timestamp(chain["snapshot_utc"].iloc[0], tz="UTC")

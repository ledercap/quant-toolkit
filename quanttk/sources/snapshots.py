"""A local Parquet archive of option-chain snapshots, so history builds up over time.

Cboe's delayed feed only shows the current chain, so changes in open interest and any
historical analysis need our own saved copies. Layout follows databases/parquet.md:

    <lake>/cboe_chains/underlying=<SYMBOL>/date=<YYYY-MM-DD>/snapshot-<HHMMSS>.parquet

`date` is the US market (America/New_York) date, so an after-the-close run at 8 pm ET files
under that trading day even though it is already the next day in UTC. HHMMSS is UTC.

The lake folder is $QUANTTK_LAKE, or `lake/` at the repo root. Parquet files are gitignored.
Requires pyarrow (pip install pyarrow).
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from quanttk.sources.cboe import ET

REPO_ROOT = Path(__file__).resolve().parents[2]


def lake_dir() -> Path:
    return Path(os.environ.get("QUANTTK_LAKE", REPO_ROOT / "lake"))


def _folder(symbol: str) -> Path:
    return lake_dir() / "cboe_chains" / f"underlying={symbol.strip('_')}"


def save_snapshot(chain: pd.DataFrame, spot: float, snapshot: pd.Timestamp, symbol: str) -> Path:
    """Save one raw Cboe chain (plus spot and snapshot time) as Parquet. Returns the file path."""
    ts = snapshot.tz_convert("UTC")
    folder = _folder(symbol) / f"date={snapshot.tz_convert(ET).date()}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"snapshot-{ts:%H%M%S}.parquet"
    out = chain.copy()
    out["spot"], out["snapshot_utc"] = spot, ts.strftime("%Y-%m-%d %H:%M:%S")
    out.to_parquet(path, index=False, compression="zstd")
    return path


def latest_snapshot_before(symbol: str, before: pd.Timestamp) -> tuple[pd.DataFrame, pd.Timestamp] | None:
    """The most recent saved snapshot from an earlier US market date than `before`, or None."""
    folder = _folder(symbol)
    if not folder.exists():
        return None
    cutoff = before.tz_convert(ET).date()
    files = sorted(p for p in folder.glob("date=*/snapshot-*.parquet")
                   if pd.Timestamp(p.parent.name.split("=", 1)[1]).date() < cutoff)
    if not files:
        return None
    df = pd.read_parquet(files[-1])
    return df, pd.Timestamp(df["snapshot_utc"].iloc[0], tz="UTC")

"""Regression tests: each workflow's offline --sample run must reproduce its saved output.

The golden files were captured from the workflows before they were refactored onto
quanttk, so these tests prove the refactor changed no results. If a change is intended,
regenerate the golden files and explain why in the pull request.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "golden"

CASES = [
    # workflow folder, extra args, golden stdout, [(output csv, golden csv)]
    ("workflows/financial-analysis/income-statement", ["--as-of", "2026-10-22"], "income-statement.txt",
     [("income_statement_sample.csv", "income_statement_sample.csv")]),
    ("workflows/options/greeks", [], "greeks.txt", [("greeks_sample.csv", "greeks_sample.csv")]),
    ("workflows/options/gamma", [], "gamma.txt",
     [("gex_by_strike_sample.csv", "gex_by_strike_sample.csv"), ("gex_sensitivity_sample.csv", "gex_sensitivity_sample.csv")]),
]


@pytest.mark.parametrize("folder,args,stdout_file,csvs", CASES, ids=[c[0].split("/")[-1] for c in CASES])
def test_sample_run_matches_golden(folder, args, stdout_file, csvs):
    wf = ROOT / folder
    run = subprocess.run([sys.executable, "-W", "ignore", "main.py", "--sample", *args], cwd=wf,
                         capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stderr
    assert run.stdout == (GOLDEN / stdout_file).read_text()
    for produced, golden in csvs:
        got = pd.read_csv(wf / "output" / produced)
        want = pd.read_csv(GOLDEN / "sample" / golden)
        pd.testing.assert_frame_equal(got, want, check_exact=False, rtol=1e-9)

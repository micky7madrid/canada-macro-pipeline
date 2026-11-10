import sys
sys.path.insert(0, "src")

import pandas as pd
from checks import check_no_duplicates, check_no_missing_values, check_gaps, check_freshness


def test_duplicates_are_caught():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-11-03", "2026-11-03"]),
        "indicator_code": ["V39079", "V39079"],
        "value": [2.25, 2.25],
    })
    result = check_no_duplicates(df)
    assert not result["passed"]


def test_clean_data_passes():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-11-03", "2026-11-04"]),
        "indicator_code": ["V39079", "V39079"],
        "value": [2.25, 2.25],
    })
    result = check_no_duplicates(df)
    assert result["passed"]

def test_missing_value_is_caught():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-11-03", "2026-11-04"]),
        "indicator_code": ["V39079", "V39079"],
        "value": [2.25, None],
    })
    assert not check_no_missing_values(df)["passed"]


def test_big_gap_is_caught():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-11-02", "2026-11-20"]),
        "indicator_code": ["V39079", "V39079"],
        "value": [2.25, 2.25],
    })
    assert not check_gaps(df)["passed"]


def test_stale_data_is_caught():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-01"]),
        "indicator_code": ["V39079"],
        "value": [2.25],
    })
    assert not check_freshness(df)["passed"]
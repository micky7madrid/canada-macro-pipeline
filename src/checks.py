import os
import pandas as pd

VALUE_RANGES = {"V39079": (0, 20),"FXUSDCAD": (0.5, 2.5),}
JUMP_LIMITS = {"FXUSDCAD": 0.03,}
MAX_GAP_DAYS = {"V41690973": 35, "STATIC_ATABLE_V35014A": 35}
MAX_AGE_DAYS = {"V41690973": 80, "STATIC_ATABLE_V35014A": 80}

def make_result(name, problems):
    return {
        "check": name,
        "passed" : len(problems)==0,
        "detail": "; ".join(problems) if problems else "ok",  
    }

def check_no_duplicates(df):
    dups = int(df.duplicated(subset=["date", "indicator_code"]).sum())
    problems = [f"{dups} duplicate rows"] if dups else []
    return make_result("no_duplicates", problems)

def check_no_missing_values(df):
    missing = int(df["value"].isna().sum())
    problems = [f"{missing} missing values"] if missing else []
    return make_result("no_missing_values", problems)

def check_value_ranges(df):
    problems = []
    for code, (low,high) in VALUE_RANGES.items():
        values = df.loc[df["indicator_code"] == code, "value"]
        bad = int(((values < low) | (values > high)).sum())
        if bad:
            problems.append(f"{code}: {bad} values outside {low} to {high}")
    return make_result("values_in_range", problems)

def check_gaps(df, max_days=5):
    problems = []
    for code, group in df.groupby("indicator_code"):
        gaps = group["date"].sort_values().diff().dt.days
        biggest = gaps.max()
        limit = MAX_GAP_DAYS.get(code, max_days)
        if biggest > limit:
            problems.append(f"{code}: gap of {int(biggest)} days")
    return make_result("no_big_gaps", problems)

def check_jumps(df):
    problems = []
    for code, limit in JUMP_LIMITS.items():
        group = df[df["indicator_code"] == code].sort_values("date")
        changes = group["value"].pct_change().abs()
        bad = int((changes > limit).sum())
        if bad:
            problems.append(f"{code}: {bad} daily changes over {limit:.0%}")
    return make_result("no_big_jumps", problems)
            
def check_freshness(df, max_age_days=5):
    problems = []
    today = pd.Timestamp.today().normalize()
    for code, group in df.groupby("indicator_code"):
        age = (today - group["date"].max()).days
        limit = MAX_AGE_DAYS.get(code, max_age_days)
        if age > limit:
            problems.append(f"{code}: latest data is {age} days old")
    return make_result("data_is_fresh", problems)

def run_all_checks(df):
    results = [
        check_no_duplicates(df),
        check_no_missing_values(df),
        check_value_ranges(df),
        check_gaps(df),
        check_jumps(df),
        check_freshness(df),
    ]
    report = pd.DataFrame(results)
    report["checked_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return report

if __name__ == "__main__":
    from clean import build_table, SERIES_IDS

    df = build_table(SERIES_IDS)
    report = run_all_checks(df)
    print()
    print(report[["check", "passed", "detail"]].to_string(index=False))

    os.makedirs("logs", exist_ok=True)
    report.to_csv("logs/data_quality_report.csv", index=False)
    print()
    print("Report saved to logs/data_quality_report.csv")
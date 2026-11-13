import sys

from clean import build_table, SERIES_IDS
from checks import run_all_checks
from load_data import load


def main():
    print("STEP 1: fetch and clean")
    df = build_table(SERIES_IDS)

    print("\nSTEP 2: quality checks")
    report = run_all_checks(df)
    print(report.to_string(index=False))

    if not report["passed"].all():
        print("\nChecks FAILED. Nothing was loaded.")
        sys.exit(1)

    print("\nSTEP 3: load into Azure SQL")
    load(df)

    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
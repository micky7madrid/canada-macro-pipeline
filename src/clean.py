import pandas as pd
from ingest import fetch_series
SERIES_IDS = ["V39079", "FXUSDCAD"]

def build_table(series_ids,recent=300):
    frames = []
    for sid in series_ids:
        details,observations = fetch_series(sid,recent=recent)
        print(f"{sid} : {details['label']} ({len(observations)} rows)")
        rows = []
        for o in observations:
            if sid in o:
                rows.append({"date": o["d"], "indicator_code": sid, "value": o[sid]["v"]})
        frames.append(pd.DataFrame(rows))

    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = (
        df.drop_duplicates(subset=["date", "indicator_code"])
        .sort_values(["indicator_code","date"])
        .reset_index(drop=True)
    )
    return df

if __name__ == "__main__":
    df = build_table(SERIES_IDS)
    print()
    print(df.head())
    print()
    print(df.dtypes)
    print()
    print(df.groupby("indicator_code")["date"].agg(["min", "max", "count"]))
    print()
    print("Missing values:", df["value"].isna().sum())
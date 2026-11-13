import os
import pyodbc
from dotenv import load_dotenv

from ingest import fetch_series
from clean import build_table, SERIES_IDS

load_dotenv()


def get_connection():
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{os.environ['AZURE_SQL_SERVER']},1433;"
        f"Database={os.environ['AZURE_SQL_DATABASE']};"
        f"Uid={os.environ['AZURE_SQL_USER']};"
        f"Pwd={os.environ['AZURE_SQL_PASSWORD']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
    )
    return pyodbc.connect(conn_str)


def load(df):
    df = df.dropna(subset=["value"])

    conn = get_connection()
    cursor = conn.cursor()

    # Empty the tables so the load can be re-run safely
    cursor.execute("DELETE FROM fact_indicator")
    cursor.execute("DELETE FROM dim_indicator")
    cursor.execute("DELETE FROM dim_date")
    cursor.execute("DELETE FROM dim_source")

    # dim_source: one row
    cursor.execute(
        "INSERT INTO dim_source (source_id, source_name, source_url) VALUES (?, ?, ?)",
        1, "Bank of Canada", "https://www.bankofcanada.ca/valet/",
    )

    # dim_indicator: one row per series code
    for code in SERIES_IDS:
        details, _ = fetch_series(code, recent=1)
        cursor.execute(
            "INSERT INTO dim_indicator (indicator_code, indicator_name, frequency, source_id) "
            "VALUES (?, ?, ?, ?)",
            code, details["label"], details.get("dateFormat", "unknown").capitalize(), 1,
        )

    # dim_date: one row per unique date
    for d in sorted(df["date"].unique()):
        d = d.to_pydatetime()
        cursor.execute(
            "INSERT INTO dim_date (date_key, full_date, year, quarter, month, month_name, day_of_week) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            int(d.strftime("%Y%m%d")), d.date(), d.year, (d.month - 1) // 3 + 1,
            d.month, d.strftime("%B"), d.strftime("%A"),
        )

    # fact_indicator: one row per (date, indicator, value)
    for row in df.itertuples():
        cursor.execute(
            "INSERT INTO fact_indicator (date_key, indicator_code, value) VALUES (?, ?, ?)",
            int(row.date.strftime("%Y%m%d")), row.indicator_code, float(row.value),
        )

    conn.commit()

    for table in ["dim_source", "dim_indicator", "dim_date", "fact_indicator"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        print(table, "->", cursor.fetchone()[0], "rows")

    conn.close()


if __name__ == "__main__":
    load(build_table(SERIES_IDS))
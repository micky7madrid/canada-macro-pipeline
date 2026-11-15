import altair as alt
import pandas as pd
import streamlit as st

from load_data import get_connection

st.set_page_config(page_title="Canada Macro Dashboard", page_icon="📈", layout="wide")

NAVY = "#1f4e79"
ORANGE = "#d9822b"
POLICY = "V39079"
FX = "FXUSDCAD"
YIELD10 = "BD.CDN.10YR.DQ.YLD"
CPI = "V41690973"
EARN = "STATIC_ATABLE_V35014A"

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    .stAppDeployButton, [data-testid="stToolbar"] {display: none;}
    .block-container {padding-top: 4rem; max-width: 1300px;}
    .banner {
        background: linear-gradient(120deg, #12365a 0%, #1f6fb5 100%);
        color: #ffffff; padding: 1.5rem 1.8rem; border-radius: 14px; margin-bottom: 1rem;
    }
    .banner h1 {color: #ffffff; margin: 0; padding: 0; font-size: 2rem;}
    .banner p {color: #dbe9f7; margin: 0.35rem 0 0 0; font-size: 1rem;}
    </style>
    <div class="banner">
        <h1>Canada Macro Dashboard</h1>
        <p>Interest rates, inflation, currency and wages in one view &nbsp;·&nbsp; Source: Bank of Canada</p>
    </div>
    """,
    unsafe_allow_html=True,
)

FACTS_SQL = """
SELECT d.full_date, i.indicator_name, i.frequency, f.indicator_code, f.value
FROM fact_indicator f
JOIN dim_date d      ON f.date_key = d.date_key
JOIN dim_indicator i ON f.indicator_code = i.indicator_code
ORDER BY d.full_date
"""


@st.cache_data(ttl=600)
def load_facts():
    conn = get_connection()
    df = pd.read_sql(FACTS_SQL, conn)
    conn.close()
    df["full_date"] = pd.to_datetime(df["full_date"])
    df["value"] = df["value"].astype(float)
    return df


try:
    facts = load_facts()
except Exception as exc:
    st.error(
        "Could not reach the database. It may be waking from auto-pause (try again in a minute), "
        "or this network may not be allowed in the Azure firewall."
    )
    with st.expander("Technical details"):
        st.code(str(exc)[:400])
    st.stop()


def series(code):
    return facts[facts["indicator_code"] == code].sort_values("full_date").reset_index(drop=True)


def prior_value(s, days=30):
    cutoff = s["full_date"].iloc[-1] - pd.Timedelta(days=days)
    older = s[s["full_date"] <= cutoff]
    return float(older["value"].iloc[-1]) if len(older) else None


def kpi(col, label, s, fmt=".2f", suffix="", dsuffix=""):
    latest = s.iloc[-1]
    prev = prior_value(s)
    delta = None if prev is None else f"{latest['value'] - prev:+{fmt}}{dsuffix}"
    col.metric(
        label,
        f"{latest['value']:{fmt}}{suffix}",
        delta,
        delta_color="off",
        border=True,
        help=f"Latest data point: {latest['full_date']:%b %d, %Y}. Change shown versus about 30 days earlier.",
    )


def line_chart(s, title, ytitle="", step=False, fmt=".2f", height=290, marks=None):
    base = alt.Chart(s).encode(
        x=alt.X("full_date:T", title=None, axis=alt.Axis(format="%b %Y", labelAngle=0, grid=False)),
        y=alt.Y("value:Q", title=ytitle, scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("full_date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("value:Q", title=title, format=fmt),
        ],
    )
    layers = [base.mark_line(color=NAVY, strokeWidth=2.5, interpolate="step-after" if step else "linear")]
    if marks is not None and len(marks):
        layers.append(
            alt.Chart(marks)
            .mark_point(color=ORANGE, size=110, filled=True)
            .encode(
                x="full_date:T",
                y="value:Q",
                tooltip=[
                    alt.Tooltip("full_date:T", title="Change date", format="%b %d, %Y"),
                    alt.Tooltip("previous_rate:Q", title="From", format=".2f"),
                    alt.Tooltip("value:Q", title="To", format=".2f"),
                ],
            )
        )
    chart = (
        alt.layer(*layers)
        .properties(height=height, title=title)
        .configure_view(strokeWidth=0)
        .configure_axis(labelFontSize=11, titleFontSize=11)
        .configure_title(fontSize=15, anchor="start", color=NAVY)
    )
    st.altair_chart(chart, width="stretch")


# ---------- prepared data ----------
policy = series(POLICY)
fx = series(FX)
y10 = series(YIELD10)
earn = series(EARN)
cpi = series(CPI)
cpi["yoy"] = cpi["value"].pct_change(12) * 100
cpi_yoy = (
    cpi.dropna(subset=["yoy"])[["full_date", "yoy"]].rename(columns={"yoy": "value"}).reset_index(drop=True)
)

policy["previous_rate"] = policy["value"].shift(1)
changes = policy[policy["value"] != policy["previous_rate"]].dropna(subset=["previous_rate"]).copy()
changes["change"] = changes["value"] - changes["previous_rate"]

# data freshness (same rules as the SQL check and the Python pipeline checks)
today = pd.Timestamp.today().normalize()
fresh = (
    facts.groupby(["indicator_name", "frequency"])["full_date"]
    .max()
    .reset_index()
    .rename(columns={"full_date": "latest_date"})
)
fresh["days_old"] = (today - fresh["latest_date"]).dt.days
limits = {"Daily": 5, "Monthly": 80}
fresh["status"] = fresh.apply(
    lambda r: "OK" if r["days_old"] <= limits.get(r["frequency"], 5) else "STALE", axis=1
)
all_fresh = bool((fresh["status"] == "OK").all())

# ---------- sidebar ----------
st.sidebar.header("View options")
WINDOWS = {"3 months": 92, "6 months": 183, "1 year": 365, "All data": None}
window = st.sidebar.radio("Time window (daily charts)", list(WINDOWS), index=2)
st.sidebar.caption(f"Latest data point: {facts['full_date'].max():%b %d, %Y}")
st.sidebar.caption("Source: Bank of Canada Valet API")


def windowed(s):
    days = WINDOWS[window]
    if days is None:
        return s
    return s[s["full_date"] >= s["full_date"].max() - pd.Timedelta(days=days)]


# ---------- status + KPI cards ----------
if all_fresh:
    st.success("Data status: all indicators are up to date")
else:
    st.warning("Data status: one or more indicators are out of date (see Data quality tab)")

c1, c2, c3, c4, c5 = st.columns(5)
kpi(c1, "Policy rate", policy, ".2f", "%", " pp")
kpi(c2, "USD/CAD", fx, ".3f")
kpi(c3, "10-year bond yield", y10, ".2f", "%", " pp")
kpi(c4, "Inflation (CPI, YoY)", cpi_yoy, ".2f", "%", " pp")
kpi(c5, "Hourly earnings", earn, ".1f", "%", " pp")

tab_overview, tab_explore, tab_rate, tab_quality, tab_about = st.tabs(
    ["Overview", "Explore", "Policy rate changes", "Data quality", "About"]
)

# ---------- Overview ----------
with tab_overview:
    left, right = st.columns(2)
    with left:
        p = windowed(policy)
        line_chart(
            p, "Policy rate (target overnight rate)", "Percent", step=True,
            marks=changes[changes["full_date"] >= p["full_date"].min()],
        )
    with right:
        line_chart(windowed(fx), "USD/CAD exchange rate", "CAD per USD", fmt=".3f")
    left, right = st.columns(2)
    with left:
        line_chart(windowed(y10), "Government of Canada 10-year bond yield", "Percent")
    with right:
        line_chart(cpi_yoy.tail(24), "Inflation: CPI change vs same month a year earlier", "Percent")
    st.caption(
        "Orange markers on the policy-rate chart are the dates the rate changed. "
        "The first and last months of the data window can be partial months."
    )

# ---------- Explore ----------
with tab_explore:
    names = sorted(facts["indicator_name"].unique())
    pick, dates_col = st.columns([1, 1])
    choice = pick.selectbox("Indicator", names)
    one = facts[facts["indicator_name"] == choice].sort_values("full_date")
    lo, hi = one["full_date"].min().date(), one["full_date"].max().date()
    dates = dates_col.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
    if len(dates) == 2:
        start, end = dates
        sel = one[(one["full_date"].dt.date >= start) & (one["full_date"].dt.date <= end)]
        if sel.empty:
            st.warning("No data in this date range.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Latest", f"{sel['value'].iloc[-1]:.3f}", border=True)
            m2.metric("Lowest", f"{sel['value'].min():.3f}", border=True)
            m3.metric("Highest", f"{sel['value'].max():.3f}", border=True)
            m4.metric("Average", f"{sel['value'].mean():.3f}", border=True)
            line_chart(sel, choice, fmt=".3f", height=360)
            st.download_button(
                "Download this selection (CSV)",
                sel[["full_date", "indicator_name", "value"]].to_csv(index=False),
                file_name="selection.csv",
                mime="text/csv",
            )

# ---------- Policy rate changes ----------
with tab_rate:
    if changes.empty:
        st.info("No policy-rate changes in the loaded data.")
    else:
        last = changes.iloc[-1]
        verb = "raised" if last["change"] > 0 else "cut"
        st.info(
            f"{len(changes)} change(s) in the loaded data. Most recent: the rate was {verb} by "
            f"{abs(last['change']):.2f} percentage points to {last['value']:.2f}% on "
            f"{last['full_date']:%b %d, %Y}."
        )
        table = changes.assign(date=changes["full_date"].dt.date).rename(
            columns={"value": "new_rate"}
        )[["date", "previous_rate", "new_rate", "change"]]
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                c: st.column_config.NumberColumn(format="%.2f")
                for c in ["previous_rate", "new_rate", "change"]
            },
        )
    line_chart(policy, "Policy rate (target overnight rate)", "Percent", step=True, marks=changes)
    st.caption(f"The loaded data starts in {policy['full_date'].min():%b %Y}, so earlier changes are not visible.")

# ---------- Data quality ----------
with tab_quality:
    st.subheader("Freshness of stored data")
    show = fresh.assign(latest_date=fresh["latest_date"].dt.date)
    st.dataframe(show, hide_index=True, width="stretch")
    st.caption(
        "Daily series are flagged stale after 5 days, monthly series after 80 days "
        "(monthly figures are dated the 1st of the month they measure and published weeks later)."
    )
    st.subheader("Checks run before every load")
    st.markdown(
        "- No duplicate rows\n- No missing values\n- Values inside expected ranges\n"
        "- No unexpected gaps in the dates\n- No implausible jumps\n- Data is fresh\n\n"
        "If any check fails, the pipeline stops and nothing is written to the database."
    )

# ---------- About ----------
with tab_about:
    st.subheader("How this works")
    st.markdown(
        "1. **Ingest:** a Python script pulls five Bank of Canada series from the public API.\n"
        "2. **Clean and check:** the data is standardized and passes six automated quality checks.\n"
        "3. **Load:** it is stored in an Azure SQL Database as a star schema "
        "(one fact table, three dimension tables).\n"
        "4. **Analyze:** SQL queries (joins, window functions) and this dashboard read from that database."
    )
    st.subheader("Scope and caveats")
    st.markdown(
        "- Five indicators: policy rate, USD/CAD, total CPI, 10-year bond yield, average hourly earnings.\n"
        "- Hourly earnings is shown in percent, as labelled by the data source.\n"
        "- Unemployment and housing prices are not included (they need a Statistics Canada source).\n"
        "- The data shows what happened. It does not explain why."
    )
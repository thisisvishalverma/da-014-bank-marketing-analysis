from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "bank-additional-full.csv"
TARGET_COLUMN = "y"

CATEGORICAL_COLUMNS = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "day_of_week",
    "poutcome",
]

NUMERIC_COLUMNS = [
    "age",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "emp.var.rate",
    "cons.price.idx",
    "cons.conf.idx",
    "euribor3m",
    "nr.employed",
]

SEGMENT_COLUMNS = CATEGORICAL_COLUMNS
CAMPAIGN_BUCKETS = ["1", "2", "3", "4", "5+"]
MONTH_ORDER = ["mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MIN_GROUP_RECORDS = 30


def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Normalize the UCI file without discarding valid contact records.

    The UCI file is semicolon-delimited. Literal ``unknown`` values are kept as
    an explicit category, ``?`` is converted to a missing value, numeric fields
    are parsed, and rows without a valid yes/no target are excluded from the
    response-rate denominator.
    """
    if raw.empty:
        raise ValueError("The dataset contains no records.")

    df = raw.copy()
    df.columns = [str(column).strip() for column in df.columns]
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Required target column '{TARGET_COLUMN}' was not found.")

    raw_record_count = int(len(df))
    text_columns = df.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        values = df[column].astype("string").str.strip()
        values = values.replace({"?": pd.NA})
        if column != TARGET_COLUMN:
            values = values.mask(values.str.lower().eq("unknown"), "Unknown")
        df[column] = values

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    target = df[TARGET_COLUMN].astype("string").str.strip().str.lower()
    valid_target = target.isin(["yes", "no"])
    excluded_target_rows = int((~valid_target).sum())
    df[TARGET_COLUMN] = target
    df = df.loc[valid_target].reset_index(drop=True)

    if df.empty:
        raise ValueError("No rows with a valid yes/no target remain after cleaning.")

    unknown_counts = {
        column: int(df[column].eq("Unknown").sum())
        for column in CATEGORICAL_COLUMNS
        if column in df.columns
    }
    quality = {
        "raw_records": raw_record_count,
        "retained_records": int(len(df)),
        "excluded_invalid_target_records": excluded_target_rows,
        "missing_cells_after_cleaning": int(df.isna().sum().sum()),
        "unknown_category_counts": unknown_counts,
    }
    return df, quality


def load_data(path: str | Path = DATA_PATH) -> tuple[pd.DataFrame, dict[str, object]]:
    """Read and clean the official semicolon-delimited UCI CSV."""
    data_path = Path(path)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Run "
            "`python data/download_dataset.py` from the project folder."
        )
    raw = pd.read_csv(data_path, sep=";", skipinitialspace=True)
    return clean_data(raw)


def calculate_kpis(data: pd.DataFrame) -> dict[str, int | float]:
    """Calculate the headline metrics for the currently selected records.

    Response rate = records with y == 'yes' / records with valid y in the
    current cohort. Rows represent campaign contact records, not unique people.
    """
    records = int(len(data))
    responses = int(data[TARGET_COLUMN].eq("yes").sum()) if records else 0
    rate = responses / records if records else float("nan")
    average_contacts = (
        float(data["campaign"].mean())
        if records and "campaign" in data.columns
        else float("nan")
    )
    return {
        "records": records,
        "responses": responses,
        "response_rate": rate,
        "average_campaign_contacts": average_contacts,
    }


def apply_filters(
    data: pd.DataFrame,
    categorical_filters: Mapping[str, Iterable[object]] | None = None,
    numeric_ranges: Mapping[str, tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """Apply sidebar filters and return a copy of the selected cohort."""
    filtered = data
    for column, selected_values in (categorical_filters or {}).items():
        if column not in filtered.columns:
            continue
        selected = list(selected_values)
        filtered = filtered.loc[filtered[column].isin(selected)]

    for column, bounds in (numeric_ranges or {}).items():
        if column not in filtered.columns:
            continue
        lower, upper = bounds
        filtered = filtered.loc[filtered[column].between(lower, upper, inclusive="both")]

    return filtered.copy()


def response_by_segment(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return record counts, successful responses, and response rates by group."""
    if column not in data.columns:
        raise KeyError(f"Column '{column}' is not in the current dataset.")
    if data.empty:
        return pd.DataFrame(columns=["segment", "records", "responses", "response_rate"])

    table = (
        data.groupby(column, dropna=False, observed=True)[TARGET_COLUMN]
        .agg(records="size", responses=lambda values: int(values.eq("yes").sum()))
        .reset_index()
        .rename(columns={column: "segment"})
    )
    table["response_rate"] = table["responses"] / table["records"]
    table["segment"] = table["segment"].astype("string").fillna("Missing")
    return table.sort_values(["response_rate", "records"], ascending=[False, False]).reset_index(drop=True)


def contact_frequency_table(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize outcomes by campaign contact-frequency bands.

    The UCI ``campaign`` field is the number of contacts to that record/client
    during this campaign, including the last contact.
    """
    if data.empty or "campaign" not in data.columns:
        return pd.DataFrame(columns=["contact_band", "records", "responses", "response_rate"])

    campaign = pd.to_numeric(data["campaign"], errors="coerce")
    bands = pd.Series(
        np.select(
            [campaign.eq(1), campaign.eq(2), campaign.eq(3), campaign.eq(4), campaign.ge(5)],
            CAMPAIGN_BUCKETS,
            default="Missing/other",
        ),
        index=data.index,
        dtype="string",
    )
    temporary = data.assign(_contact_band=bands)
    table = (
        temporary.groupby("_contact_band", observed=True)[TARGET_COLUMN]
        .agg(records="size", responses=lambda values: int(values.eq("yes").sum()))
        .reset_index()
        .rename(columns={"_contact_band": "contact_band"})
    )
    table["response_rate"] = table["responses"] / table["records"]
    order = {label: index for index, label in enumerate(CAMPAIGN_BUCKETS + ["Missing/other"])}
    table["_order"] = table["contact_band"].map(order)
    return table.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def generate_findings(
    data: pd.DataFrame,
    segment_column: str = "job",
    min_group_records: int = MIN_GROUP_RECORDS,
) -> list[dict[str, str]]:
    """Create descriptive, sample-size-aware findings for the selected cohort."""
    if data.empty:
        return [{
            "title": "No records in the current selection",
            "finding": "Adjust or clear filters to calculate findings.",
            "recommendation": "Review a broader cohort before making campaign decisions.",
        }]

    findings: list[dict[str, str]] = []
    segments = response_by_segment(data, segment_column)
    eligible = segments.loc[segments["records"] >= min_group_records]
    if not eligible.empty:
        top = eligible.iloc[0]
        findings.append({
            "title": f"Highest observed response: {segment_column.replace('_', ' ').title()}",
            "finding": (
                f"{top['segment']} has the highest observed rate in the selected cohort: "
                f"{top['responses']:,} of {top['records']:,} records "
                f"({top['response_rate']:.1%}). Groups below {min_group_records} records are omitted."
            ),
            "recommendation": (
                "Use this segment as a hypothesis for a targeted campaign test; this descriptive "
                "association does not establish that the segment caused the response."
            ),
        })
    else:
        findings.append({
            "title": "Segment sample is too small",
            "finding": (
                f"No {segment_column.replace('_', ' ')} group has at least "
                f"{min_group_records} records in the current selection."
            ),
            "recommendation": "Broaden the filters before comparing segment response rates.",
        })

    frequency = contact_frequency_table(data).set_index("contact_band")
    one = frequency.loc["1"] if "1" in frequency.index else None
    repeated = frequency.loc["5+"] if "5+" in frequency.index else None
    if (
        one is not None
        and repeated is not None
        and one["records"] >= min_group_records
        and repeated["records"] >= min_group_records
    ):
        higher_band = "5+ contacts" if repeated["response_rate"] > one["response_rate"] else "one contact"
        difference_pp = abs(repeated["response_rate"] - one["response_rate"]) * 100
        direction = "higher" if repeated["response_rate"] > one["response_rate"] else "lower"
        findings.append({
            "title": "Contact-frequency comparison",
            "finding": (
                f"Response was {one['response_rate']:.1%} after one contact "
                f"({int(one['records']):,} records) and {repeated['response_rate']:.1%} after "
                f"5+ contacts ({int(repeated['records']):,} records); the 5+ band was "
                f"{difference_pp:.1f} percentage points {direction}."
            ),
            "recommendation": (
                f"Review the contact cadence for the {higher_band} group before changing follow-up "
                "rules; the comparison is observational and may reflect differences in who was contacted."
            ),
        })
    else:
        findings.append({
            "title": "Contact-frequency comparison needs more records",
            "finding": (
                f"The one-contact and 5+ contact bands do not both meet the "
                f"{min_group_records}-record display threshold in the current selection."
            ),
            "recommendation": "Use the chart to inspect the available contact bands, but avoid a cadence recommendation from small groups.",
        })

    if "contact" in data.columns:
        channels = response_by_segment(data, "contact")
        channels = channels.loc[channels["records"] >= min_group_records]
        if len(channels) >= 2:
            best = channels.iloc[0]
            other = channels.iloc[-1]
            findings.append({
                "title": "Communication-channel comparison",
                "finding": (
                    f"{best['segment']} has the highest observed channel rate at {best['response_rate']:.1%} "
                    f"({int(best['responses']):,}/{int(best['records']):,}); the comparison channel "
                    f"{other['segment']} is {other['response_rate']:.1%} "
                    f"({int(other['responses']):,}/{int(other['records']):,})."
                ),
                "recommendation": "Use channel differences to design a controlled follow-up test; customer mix and campaign timing can also explain the gap.",
            })
        else:
            findings.append({
                "title": "Channel comparison needs more records",
                "finding": f"Fewer than two communication channels meet the {min_group_records}-record threshold.",
                "recommendation": "Review a larger cohort before recommending a channel shift.",
            })

    return findings


def quality_table(quality: Mapping[str, object]) -> pd.DataFrame:
    """Turn cleaning metadata into a simple table for notebook display."""
    unknown_counts = quality.get("unknown_category_counts", {})
    if not isinstance(unknown_counts, Mapping):
        unknown_counts = {}
    rows = [
        ("Rows read from CSV", quality.get("raw_records", 0)),
        ("Rows retained with valid target", quality.get("retained_records", 0)),
        ("Rows excluded for invalid target", quality.get("excluded_invalid_target_records", 0)),
        ("Missing cells after cleaning", quality.get("missing_cells_after_cleaning", 0)),
        ("Explicit Unknown categories", int(sum(unknown_counts.values()))),
    ]
    return pd.DataFrame(rows, columns=["Data-quality measure", "Value"])


st.set_page_config(
    page_title="Bank Marketing Campaign Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 2.5rem; max-width: 1500px;}
      .hero {padding: 1.35rem 1.6rem; border-radius: 16px; background: linear-gradient(115deg,#102a43,#176b87); color: white; margin-bottom: 1rem;}
      .hero p {margin-bottom: 0; color: #e5f4f8;}
      [data-testid="stMetric"] {background: #f6f9fc; border: 1px solid #e4ebf2; padding: 1rem 1.1rem; border-radius: 14px;}
      .note {color:#566575; font-size:0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading and checking the UCI dataset…")
def get_data(path: str) -> tuple[pd.DataFrame, dict[str, object]]:
    return load_data(path)


if not DATA_PATH.exists():
    try:
        from data.download_dataset import main as download_dataset

        with st.spinner("Downloading the public UCI dataset…"):
            download_dataset()
    except Exception as exc:  # The hosted app can run without a pre-bundled CSV.
        st.error("The dataset is missing and could not be downloaded from UCI.")
        st.caption("Check the app logs or download the dataset locally, then restart the app.")
        st.code("python data/download_dataset.py", language="powershell")
        st.exception(exc)
        st.stop()

try:
    data, quality = get_data(str(DATA_PATH))
except Exception as exc:  # Show a useful message in the app instead of a traceback.
    st.error(f"The dataset could not be loaded: {exc}")
    st.stop()


st.sidebar.title("DA-014 · Campaign analytics")
st.sidebar.caption("Explore response patterns in a public bank marketing dataset.")
page = st.sidebar.radio("Dashboard", ["Overview", "Data & methodology", "Findings & recommendations"])
st.sidebar.divider()
st.sidebar.subheader("Filter the campaign records")

categorical_filters: dict[str, list[object]] = {}
for column in CATEGORICAL_COLUMNS:
    if column not in data.columns:
        continue
    values = sorted(data[column].dropna().unique().tolist(), key=lambda item: str(item).lower())
    selected = st.sidebar.multiselect(column.replace("_", " ").title(), values, default=values, key=f"filter_{column}")
    categorical_filters[column] = selected

numeric_ranges: dict[str, tuple[float, float]] = {}
with st.sidebar.expander("Numeric ranges", expanded=False):
    for column in NUMERIC_COLUMNS:
        if column not in data.columns:
            continue
        series = data[column].dropna()
        if series.empty:
            continue
        low, high = float(series.min()), float(series.max())
        if low == high:
            numeric_ranges[column] = (low, high)
            st.caption(f"{column}: {low:g}")
            continue
        selected_range = st.slider(
            column.replace(".", " ").replace("_", " ").title(),
            min_value=low,
            max_value=high,
            value=(low, high),
            key=f"range_{column}",
        )
        numeric_ranges[column] = selected_range

filtered = apply_filters(data, categorical_filters, numeric_ranges)
kpis = calculate_kpis(filtered)

st.markdown(
    """
    <div class="hero">
      <h1>Bank Marketing Campaign Analysis</h1>
      <p>Project DA-014 · Marketing Analytics · Explore which observed campaign and customer segments are associated with term-deposit subscriptions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "Each row is a campaign contact record. The response rate is successful subscriptions (y = yes) divided by all records in the current filtered cohort with a valid yes/no target."
)

if page == "Overview":
    st.subheader("Campaign snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records analyzed", f"{kpis['records']:,}")
    c2.metric("Successful responses", f"{kpis['responses']:,}")
    c3.metric("Response rate", f"{kpis['response_rate']:.2%}" if pd.notna(kpis["response_rate"]) else "—")
    c4.metric("Avg. contacts in campaign", f"{kpis['average_campaign_contacts']:.2f}" if pd.notna(kpis["average_campaign_contacts"]) else "—")

    if filtered.empty:
        st.warning("No records match these filters. Widen or clear filters to see the charts.")
    else:
        left, right = st.columns(2)
        with left:
            segment_column = st.selectbox(
                "Compare response rate by segment",
                options=[column for column in SEGMENT_COLUMNS if column in filtered.columns],
                index=0,
                format_func=lambda value: value.replace("_", " ").title(),
            )
            segment_table = response_by_segment(filtered, segment_column)
            fig = px.bar(
                segment_table.sort_values("response_rate"),
                x="response_rate",
                y="segment",
                orientation="h",
                color="response_rate",
                color_continuous_scale="Teal",
                hover_data={"records": ":,", "responses": ":,", "response_rate": ":.2%"},
                labels={"response_rate": "Response rate", "segment": segment_column.replace("_", " ").title()},
                title=f"Response rate by {segment_column.replace('_', ' ')}",
            )
            fig.update_xaxes(tickformat=".0%", title="Response rate")
            fig.update_layout(coloraxis_showscale=False, margin=dict(l=8, r=8, t=55, b=10))
            st.plotly_chart(fig, width="stretch")
            st.dataframe(
                segment_table.assign(response_rate=segment_table["response_rate"].map(lambda value: f"{value:.2%}")),
                hide_index=True,
                width="stretch",
            )
        with right:
            frequency = contact_frequency_table(filtered)
            fig = px.bar(
                frequency,
                x="contact_band",
                y="response_rate",
                color="contact_band",
                hover_data={"records": ":,", "responses": ":,", "response_rate": ":.2%"},
                labels={"contact_band": "Contacts during this campaign", "response_rate": "Response rate"},
                title="Response rate by campaign contact frequency",
                category_orders={"contact_band": ["1", "2", "3", "4", "5+", "Missing/other"]},
            )
            fig.update_yaxes(tickformat=".0%", title="Response rate")
            fig.update_layout(showlegend=False, margin=dict(l=8, r=8, t=55, b=10))
            st.plotly_chart(fig, width="stretch")
            st.dataframe(
                frequency.assign(response_rate=frequency["response_rate"].map(lambda value: f"{value:.2%}")),
                hide_index=True,
                width="stretch",
            )

        st.subheader("Communication and contact timing")
        channel_col, month_col, weekday_col = st.columns(3)
        for container, column, title in [
            (channel_col, "contact", "By communication channel"),
            (month_col, "month", "By contact month"),
            (weekday_col, "day_of_week", "By weekday"),
        ]:
            with container:
                chart_data = response_by_segment(filtered, column)
                if column == "month":
                    month_rank = {month: index for index, month in enumerate(["mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
                    chart_data = chart_data.assign(_rank=chart_data["segment"].map(month_rank)).sort_values("_rank")
                elif column == "day_of_week":
                    weekday_rank = {day: index for index, day in enumerate(["mon", "tue", "wed", "thu", "fri"])}
                    chart_data = chart_data.assign(_rank=chart_data["segment"].map(weekday_rank)).sort_values("_rank")
                chart = px.bar(
                    chart_data,
                    x="segment",
                    y="response_rate",
                    hover_data={"records": ":,", "responses": ":,", "response_rate": ":.2%"},
                    labels={"segment": "", "response_rate": "Response rate"},
                    title=title,
                    color="response_rate",
                    color_continuous_scale="Teal",
                )
                chart.update_yaxes(tickformat=".0%")
                chart.update_layout(coloraxis_showscale=False, margin=dict(l=4, r=4, t=55, b=5))
                st.plotly_chart(chart, width="stretch")

    with st.expander("Preview filtered records"):
        st.caption(f"Showing up to 100 of {len(filtered):,} filtered records.")
        st.dataframe(filtered.head(100), hide_index=True, width="stretch")

elif page == "Data & methodology":
    st.subheader("Dataset and cleaning")
    st.markdown(
        "The dashboard uses the UCI Bank Marketing `bank-additional-full.csv` dataset. The target is `y`: whether a client subscribed to a term deposit (`yes` or `no`). Text values are trimmed, `?` is treated as missing, and literal `unknown` categories are preserved as `Unknown`. Only rows without a valid yes/no target are excluded from rate denominators."
    )
    st.info("Response rate = number of records where y = yes ÷ number of records with valid y in the selected cohort. The rows are contact records; the dataset does not provide a unique customer ID for deduplicating people.")
    st.warning("`duration` is the call duration in seconds and is only known after the contact. It is available as an exploratory filter, but should not be used to plan a pre-call targeting strategy.")
    st.markdown("**Data quality summary**")
    st.dataframe(pd.DataFrame([
        {"Measure": "Rows read", "Value": quality["raw_records"]},
        {"Measure": "Rows retained with valid target", "Value": quality["retained_records"]},
        {"Measure": "Rows excluded for invalid target", "Value": quality["excluded_invalid_target_records"]},
        {"Measure": "Missing cells after cleaning", "Value": quality["missing_cells_after_cleaning"]},
        {"Measure": "Explicit Unknown category cells", "Value": sum(quality["unknown_category_counts"].values())},
    ]), hide_index=True, width="stretch")
    st.markdown("**Preview**")
    st.dataframe(filtered.head(100), hide_index=True, width="stretch")
    st.caption("Source: UCI Machine Learning Repository, Bank Marketing (DOI: 10.24432/C5K306), CC BY 4.0. Full source and download instructions are in `data/SOURCE.md`.")

else:
    st.subheader("Findings and recommendations")
    st.caption("Findings recalculate from the current filters. Segment summaries require at least 30 records and describe association, not causation.")
    if filtered.empty:
        st.warning("No records match these filters. Adjust the sidebar selections.")
    else:
        for item in generate_findings(filtered):
            with st.container(border=True):
                st.markdown(f"**{item['title']}**")
                st.write(item["finding"])
                st.markdown(f"**Suggested next step:** {item['recommendation']}")
    st.markdown("#### Practical interpretation")
    st.write("Use these patterns to form testable hypotheses. Compare like-for-like cohorts and validate any proposed targeting or follow-up change with a controlled experiment before rollout.")

st.divider()
st.markdown(
    '<p class="note">Source: UCI Machine Learning Repository · Bank Marketing · Descriptive analysis only. Historical response patterns do not establish causation.</p>',
    unsafe_allow_html=True,
)

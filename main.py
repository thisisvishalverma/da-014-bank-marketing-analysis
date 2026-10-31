from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import (
    CATEGORICAL_COLUMNS,
    DATA_PATH,
    NUMERIC_COLUMNS,
    SEGMENT_COLUMNS,
    apply_filters,
    calculate_kpis,
    contact_frequency_table,
    generate_findings,
    load_data,
    response_by_segment,
)


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
        from scripts.download_dataset import main as download_dataset

        with st.spinner("Downloading the public UCI dataset…"):
            download_dataset()
    except Exception as exc:  # The hosted app can run without a pre-bundled CSV.
        st.error("The dataset is missing and could not be downloaded from UCI.")
        st.caption("Check the app logs or download the dataset locally, then restart the app.")
        st.code("python scripts/download_dataset.py", language="powershell")
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

"""Shared data loading and analysis functions for project DA-014.

Both the Streamlit dashboard and the Jupyter notebook use these functions so
that the response-rate denominator and group calculations stay consistent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd


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
            "`python scripts/download_dataset.py` from the project folder."
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

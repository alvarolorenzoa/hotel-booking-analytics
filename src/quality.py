"""Data quality: profiling of the raw data and validation rules for the clean data.

Profiling answers "what does the raw data look like?" (nulls, duplicates, outliers,
distributions). Validation answers "is the clean data safe to load?" and fails the
pipeline if a rule is broken.
"""
from dataclasses import dataclass, field

import pandas as pd

from src import config


# --------------------------------------------------------------------------- profiling
def profile(df: pd.DataFrame) -> dict:
    """Statistical profile of a dataframe: size, missing values, duplicates and outliers."""
    numeric = df.select_dtypes("number")
    q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
    iqr = q3 - q1
    outliers = ((numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)).sum()

    missing = df.isna().sum()
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing": {c: int(n) for c, n in missing[missing > 0].items()},
        "missing_pct": {c: round(100 * n / len(df), 2) for c, n in missing[missing > 0].items()},
        "iqr_outliers": {c: int(n) for c, n in outliers[outliers > 0].items()},
        "adr": df["adr"].describe().round(2).to_dict() if "adr" in df else {},
        "lead_time": df["lead_time"].describe().round(2).to_dict() if "lead_time" in df else {},
    }


# --------------------------------------------------------------------------- validation
@dataclass
class ValidationResult:
    passed: list = field(default_factory=list)
    failed: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failed


def validate_clean(df: pd.DataFrame, min_rows: int = 1) -> ValidationResult:
    """Business and technical rules the clean bookings table must satisfy."""
    rules = {
        f"row count >= {min_rows:,}": len(df) >= min_rows,
        "booking_id is unique": df["booking_id"].is_unique,
        "no nulls in key columns": df[["booking_id", "hotel", "arrival_date", "country"]].notna().all().all(),
        "adr within [0, MAX_VALID_ADR]": df["adr"].between(0, config.MAX_VALID_ADR).all(),
        "every booking has at least one guest": (df["total_guests"] > 0).all(),
        "lead_time is non-negative": (df["lead_time"] >= 0).all(),
        "is_canceled is binary": df["is_canceled"].isin([0, 1]).all(),
        "revenue is zero for cancelled bookings": (df.loc[df["is_canceled"] == 1, "revenue"] == 0).all(),
        "total_nights = weekend + week nights": (
            df["total_nights"] == df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
        ).all(),
    }
    result = ValidationResult()
    for name, passed in rules.items():
        (result.passed if passed else result.failed).append(name)
    return result


def render_report(raw_profile: dict, clean_profile: dict, removed: dict, validation: ValidationResult) -> str:
    """Markdown data quality report written to docs/data_quality_report.md."""
    lines = ["# Data Quality Report", "", "_Generated automatically by `src/pipeline.py`._", ""]
    lines += ["## 1. Raw data profile", "",
              f"- Rows: **{raw_profile['rows']:,}** · Columns: **{raw_profile['columns']}**",
              f"- Fully duplicated rows: **{raw_profile['duplicate_rows']:,}** "
              "(kept: the source has no booking ID, so identical rows are treated as separate "
              "bookings, e.g. group reservations)", "",
              "| Column | Missing values | % |", "|---|---:|---:|"]
    for col, n in raw_profile["missing"].items():
        lines.append(f"| {col} | {n:,} | {raw_profile['missing_pct'][col]} % |")
    lines += ["", "**Outliers (IQR rule) in key numeric columns**", "", "| Column | Outliers |", "|---|---:|"]
    for col in ["adr", "lead_time", "stays_in_week_nights", "days_in_waiting_list"]:
        if col in raw_profile["iqr_outliers"]:
            lines.append(f"| {col} | {raw_profile['iqr_outliers'][col]:,} |")
    a = raw_profile["adr"]
    lines += ["", f"ADR (average daily rate, €): min **{a['min']}**, median **{a['50%']}**, "
              f"max **{a['max']}**", "", "## 2. Cleaning actions", "",
              "| Rule | Rows removed |", "|---|---:|"]
    for rule, n in removed.items():
        lines.append(f"| {rule} | {n:,} |")
    lines += ["", "Imputations: `children` → 0, `country` → `UNK`, `meal` 'Undefined' → 'SC' "
              "(same meaning in the source). `agent` / `company` nulls mean *no agent / no company* "
              "and are kept as flags.", "",
              "## 3. Validation of the clean table", "",
              f"Rows after cleaning: **{clean_profile['rows']:,}**", ""]
    lines += [f"- ✅ {r}" for r in validation.passed]
    lines += [f"- ❌ {r}" for r in validation.failed]
    return "\n".join(lines) + "\n"

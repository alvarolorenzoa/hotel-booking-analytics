"""Transform step: clean the raw bookings and derive business features."""
import logging

import pandas as pd

from src import config

log = logging.getLogger(__name__)

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}

SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}

LEAD_TIME_BINS = [-1, 7, 30, 90, 180, 365, 10_000]
LEAD_TIME_LABELS = ["0-7 days", "8-30 days", "31-90 days", "91-180 days", "181-365 days", "365+ days"]


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply cleaning rules. Returns the clean dataframe and the rows removed per rule."""
    df = raw.copy()
    removed = {}

    # 1. Imputations (documented in the data quality report)
    df["children"] = df["children"].fillna(0).astype(int)
    df["country"] = df["country"].fillna("UNK")
    df["meal"] = df["meal"].replace("Undefined", "SC")
    df["has_agent"] = df["agent"].notna().astype(int)
    df["has_company"] = df["company"].notna().astype(int)

    # 2. Remove invalid records
    guests = df["adults"] + df["children"] + df["babies"]
    mask = guests == 0
    removed["Bookings with zero guests"] = int(mask.sum())
    df = df[~mask]

    mask = df["adr"] < 0
    removed["Negative ADR"] = int(mask.sum())
    df = df[~mask]

    mask = df["adr"] > config.MAX_VALID_ADR
    removed[f"ADR above {config.MAX_VALID_ADR:.0f} € (data-entry error)"] = int(mask.sum())
    df = df[~mask]

    log.info("Cleaning removed %s rows", sum(removed.values()))
    return df.reset_index(drop=True), removed


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the business features used by the model, the SQL layer and the dashboard."""
    df = df.copy()
    df.insert(0, "booking_id", range(1, len(df) + 1))

    df["arrival_date"] = pd.to_datetime(dict(
        year=df["arrival_date_year"],
        month=df["arrival_date_month"].map(MONTHS),
        day=df["arrival_date_day_of_month"],
    ))
    df["booking_date"] = df["arrival_date"] - pd.to_timedelta(df["lead_time"], unit="D")
    df["reservation_status_date"] = pd.to_datetime(df["reservation_status_date"])

    df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["total_guests"] = df["adults"] + df["children"] + df["babies"]
    df["is_family"] = ((df["children"] + df["babies"]) > 0).astype(int)
    df["room_changed"] = (df["reserved_room_type"] != df["assigned_room_type"]).astype(int)

    # Realised revenue only counts stays that were not cancelled
    df["revenue"] = (df["adr"] * df["total_nights"]).where(df["is_canceled"] == 0, 0.0).round(2)
    # Revenue at risk: value of the bookings that were eventually cancelled
    df["lost_revenue"] = (df["adr"] * df["total_nights"]).where(df["is_canceled"] == 1, 0.0).round(2)

    df["season"] = df["arrival_date"].dt.month.map(SEASONS)
    buckets = pd.cut(df["lead_time"], LEAD_TIME_BINS, labels=LEAD_TIME_LABELS)
    df["lead_time_bucket"] = buckets.astype(str)
    df["lead_time_bucket_order"] = buckets.cat.codes + 1   # sort key for Power BI visuals
    return df


def transform(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df, removed = clean(raw)
    return add_features(df), removed

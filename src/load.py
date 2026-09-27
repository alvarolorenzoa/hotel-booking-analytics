"""Load step: stage the clean data in DuckDB, build the star schema and export it.

The Parquet files in data/processed/ are what Power BI reads.
"""
import logging
from pathlib import Path

import duckdb
import pandas as pd

from src import config

log = logging.getLogger(__name__)

STAR_TABLES = ["fact_bookings", "dim_date", "dim_hotel", "dim_country", "dim_channel", "dim_customer"]

# Codes in the source that are not ISO 3166 alpha-3
EXTRA_COUNTRY_NAMES = {"CN": "China", "TMP": "East Timor", "UNK": "Unknown"}


def country_names(codes) -> pd.DataFrame:
    """Map ISO alpha-3 codes to country names (uses pycountry when available)."""
    try:
        import pycountry
    except ImportError:  # the pipeline still works, dim_country falls back to the code
        pycountry = None
    rows = []
    for code in codes:
        name = EXTRA_COUNTRY_NAMES.get(code)
        if name is None and pycountry is not None:
            match = pycountry.countries.get(alpha_3=code)
            name = match.name if match else None
        rows.append({"country_code": code, "country_name": name})
    return pd.DataFrame(rows)


def build_warehouse(clean: pd.DataFrame, db_file: Path = config.DB_FILE) -> duckdb.DuckDBPyConnection:
    """Create the DuckDB warehouse: staging tables + star schema."""
    db_file.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_file))
    con.register("clean_df", clean)
    con.execute("CREATE OR REPLACE TABLE stg_bookings AS SELECT * FROM clean_df")
    con.register("country_df", country_names(clean["country"].unique()))
    con.execute("CREATE OR REPLACE TABLE stg_country_names AS SELECT * FROM country_df")

    con.execute((config.SQL_DIR / "01_star_schema.sql").read_text())
    for t in STAR_TABLES:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        log.info("Loaded %-14s %s rows", t, f"{n:,}")
    return con


def check_referential_integrity(con: duckdb.DuckDBPyConnection) -> dict:
    """Every foreign key in the fact table must exist in its dimension (0 orphans expected)."""
    checks = {
        "arrival_date_key": "SELECT COUNT(*) FROM fact_bookings f LEFT JOIN dim_date d ON f.arrival_date_key = d.date_key WHERE d.date_key IS NULL",
        "booking_date_key": "SELECT COUNT(*) FROM fact_bookings f LEFT JOIN dim_date d ON f.booking_date_key = d.date_key WHERE d.date_key IS NULL",
        "hotel_key": "SELECT COUNT(*) FROM fact_bookings f LEFT JOIN dim_hotel d USING (hotel_key) WHERE d.hotel_key IS NULL",
        "country_key": "SELECT COUNT(*) FROM fact_bookings f LEFT JOIN dim_country d USING (country_key) WHERE d.country_key IS NULL",
        "channel_key": "SELECT COUNT(*) FROM fact_bookings f LEFT JOIN dim_channel d USING (channel_key) WHERE d.channel_key IS NULL",
        "customer_key": "SELECT COUNT(*) FROM fact_bookings f LEFT JOIN dim_customer d USING (customer_key) WHERE d.customer_key IS NULL",
    }
    return {k: con.execute(q).fetchone()[0] for k, q in checks.items()}


def export_parquet(con: duckdb.DuckDBPyConnection, out_dir: Path = config.PROCESSED_DIR) -> None:
    """Export every star-schema table to Parquet for Power BI."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for t in STAR_TABLES:
        con.execute(f"COPY {t} TO '{(out_dir / f'{t}.parquet').as_posix()}' (FORMAT PARQUET)")
    log.info("Exported %d tables to %s", len(STAR_TABLES), out_dir)

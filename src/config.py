"""Central configuration: paths, data source and data quality thresholds."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SQL_DIR = ROOT / "sql"
DOCS_DIR = ROOT / "docs"
IMG_DIR = DOCS_DIR / "img"

RAW_FILE = RAW_DIR / "hotel_bookings.csv"
DB_FILE = DATA_DIR / "hotel_analytics.duckdb"

# Public dataset: Antonio, Almeida & Nunes (2019), "Hotel booking demand datasets",
# Data in Brief 22, 41-49 (CC BY 4.0). Mirrored by the TidyTuesday project.
SOURCE_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/"
    "master/data/2020/2020-02-11/hotels.csv"
)

# Data quality rules
MAX_VALID_ADR = 1000.0      # average daily rate above this is treated as a data-entry error
MIN_EXPECTED_ROWS = 100_000  # sanity check on the full extract

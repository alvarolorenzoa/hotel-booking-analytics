"""Extract step: download the raw bookings file (only if missing) and read it."""
import logging
import urllib.request
from pathlib import Path

import pandas as pd

from src import config

log = logging.getLogger(__name__)


def download_raw(url: str = config.SOURCE_URL, dest: Path = config.RAW_FILE, force: bool = False) -> Path:
    """Download the source CSV to data/raw. Skips the download if the file already exists."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        log.info("Raw file already present: %s", dest.name)
        return dest
    log.info("Downloading raw data from %s", url)
    urllib.request.urlretrieve(url, dest)
    return dest


def read_raw(path: Path = config.RAW_FILE) -> pd.DataFrame:
    """Read the raw CSV. The source encodes missing values as the string 'NULL'."""
    df = pd.read_csv(path, na_values=["NULL"], low_memory=False)
    log.info("Extracted %s rows x %s columns", f"{len(df):,}", df.shape[1])
    return df

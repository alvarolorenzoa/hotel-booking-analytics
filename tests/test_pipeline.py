"""Unit tests for the ETL pipeline. They run on a small fixture, so no download is needed (used in CI)."""
from pathlib import Path

import pytest

from src import extract, load, quality, transform
from src.analysis import load_queries

FIXTURE = Path(__file__).parent / "fixtures" / "sample_bookings.csv"


@pytest.fixture(scope="module")
def raw():
    return extract.read_raw(FIXTURE)


@pytest.fixture(scope="module")
def clean(raw):
    df, _ = transform.transform(raw)
    return df


def test_invalid_rows_are_removed(raw):
    df, removed = transform.transform(raw)
    assert removed["Bookings with zero guests"] >= 3
    assert removed["Negative ADR"] == 1
    assert len(df) == len(raw) - sum(removed.values())


def test_no_missing_values_in_imputed_columns(clean):
    assert clean["children"].notna().all()
    assert clean["country"].notna().all()
    assert "Undefined" not in set(clean["meal"])


def test_revenue_only_for_non_cancelled(clean):
    assert (clean.loc[clean["is_canceled"] == 1, "revenue"] == 0).all()
    assert (clean.loc[clean["is_canceled"] == 0, "lost_revenue"] == 0).all()
    ok = clean[clean["is_canceled"] == 0]
    assert (ok["revenue"] - (ok["adr"] * ok["total_nights"]).round(2)).abs().max() < 0.01


def test_booking_date_is_before_arrival(clean):
    assert (clean["booking_date"] <= clean["arrival_date"]).all()


def test_validation_rules_pass(clean):
    result = quality.validate_clean(clean)
    assert result.ok, result.failed


def test_validation_catches_bad_data(clean):
    bad = clean.copy()
    bad.loc[0, "adr"] = -50
    assert not quality.validate_clean(bad).ok


def test_star_schema_integrity(clean, tmp_path):
    con = load.build_warehouse(clean, db_file=tmp_path / "test.duckdb")
    assert con.execute("SELECT COUNT(*) FROM fact_bookings").fetchone()[0] == len(clean)
    assert not any(load.check_referential_integrity(con).values())
    con.close()


def test_business_queries_run(clean, tmp_path):
    con = load.build_warehouse(clean, db_file=tmp_path / "test.duckdb")
    queries = load_queries()
    assert len(queries) >= 8
    for name, sql in queries.items():
        assert con.execute(sql).df() is not None, name
    con.close()

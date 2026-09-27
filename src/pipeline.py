"""End-to-end ETL pipeline.

Usage (from the project root):
    python -m src.pipeline
"""
import logging
import sys
import time

from src import config, extract, load, quality, transform

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("pipeline")


def run() -> None:
    t0 = time.perf_counter()

    # Extract
    extract.download_raw()
    raw = extract.read_raw()
    raw_profile = quality.profile(raw)

    # Transform
    clean, removed = transform.transform(raw)
    clean_profile = quality.profile(clean)

    # Validate (fail fast: nothing is loaded if a rule is broken)
    validation = quality.validate_clean(clean, min_rows=config.MIN_EXPECTED_ROWS)
    report = quality.render_report(raw_profile, clean_profile, removed, validation)
    config.DOCS_DIR.mkdir(exist_ok=True)
    (config.DOCS_DIR / "data_quality_report.md").write_text(report, encoding="utf-8")
    if not validation.ok:
        log.error("Validation failed: %s", validation.failed)
        sys.exit(1)
    log.info("Validation passed (%d rules)", len(validation.passed))

    # Load
    con = load.build_warehouse(clean)
    orphans = load.check_referential_integrity(con)
    if any(orphans.values()):
        log.error("Referential integrity broken: %s", orphans)
        sys.exit(1)
    log.info("Referential integrity OK (0 orphan keys)")
    load.export_parquet(con)
    con.close()

    log.info("Pipeline finished in %.1f s", time.perf_counter() - t0)


if __name__ == "__main__":
    run()

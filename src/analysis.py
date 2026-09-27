"""Run the business SQL queries against the warehouse and write results + charts.

Usage (after the pipeline):
    python -m src.analysis
"""
import logging
import re

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src import config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("analysis")
logging.getLogger("matplotlib").setLevel(logging.WARNING)

plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "font.size": 10})
BLUE, ORANGE, GREY = "#1F3864", "#E07A1F", "#9AA5B1"


def load_queries(path=config.SQL_DIR / "02_business_queries.sql") -> dict[str, str]:
    """Split the SQL file into {query_name: sql} using the '-- name:' markers."""
    parts = re.split(r"^-- name:\s*(\w+)\s*$", path.read_text(), flags=re.M)
    return {parts[i]: parts[i + 1].strip().rstrip(";") for i in range(1, len(parts), 2)}


def fmt(v) -> str:
    if pd.isna(v):
        return ""
    if isinstance(v, (int,)) or (isinstance(v, float) and v.is_integer() and abs(v) >= 1000):
        return f"{int(v):,}"
    return str(v)


def to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(out)


def save(fig, name: str) -> None:
    config.IMG_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(config.IMG_DIR / name, bbox_inches="tight")
    plt.close(fig)


def charts(r: dict[str, pd.DataFrame]) -> None:
    df = r["cancellation_by_lead_time"]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    bars = ax.bar(df["lead_time_bucket"], df["cancellation_rate_pct"], color=BLUE)
    ax.bar_label(bars, fmt="%.0f%%", padding=2)
    ax.set(title="Cancellation rate by booking lead time", ylabel="% cancelled")
    save(fig, "cancellation_by_lead_time.png")

    df = r["seasonality_adr"]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(df["month_name"], df["city_adr"], marker="o", color=BLUE, label="City Hotel")
    ax.plot(df["month_name"], df["resort_adr"], marker="o", color=ORANGE, label="Resort Hotel")
    ax.set(title="Average daily rate (ADR) by arrival month", ylabel="ADR (€)")
    ax.legend(frameon=False)
    save(fig, "adr_seasonality.png")

    df = r["segment_performance"].sort_values("revenue_k")
    fig, ax = plt.subplots(figsize=(7, 3.6))
    bars = ax.barh(df["market_segment"], df["revenue_k"], color=BLUE)
    ax.bar_label(bars, labels=[f"{v:,.0f}k€ · {c}% canc." for v, c in
                               zip(df["revenue_k"], df["cancellation_rate_pct"])], padding=3, fontsize=8)
    ax.set(title="Realised revenue by market segment", xlabel="Revenue (k€)")
    ax.set_xlim(0, df["revenue_k"].max() * 1.35)
    save(fig, "revenue_by_segment.png")


def run() -> None:
    con = duckdb.connect(str(config.DB_FILE), read_only=True)
    results = {}
    md = ["# Business Insights", "", "_Generated automatically by `src/analysis.py` from "
          "`sql/02_business_queries.sql`._", ""]
    for name, sql in load_queries().items():
        df = con.execute(sql).df()
        results[name] = df
        title = name.replace("_", " ").capitalize()
        md += [f"## {title}", "", to_markdown(df), ""]
        log.info("Query %-28s -> %d rows", name, len(df))
    con.close()
    (config.DOCS_DIR / "business_insights.md").write_text("\n".join(md), encoding="utf-8")
    charts(results)
    log.info("Wrote docs/business_insights.md and charts to docs/img/")


if __name__ == "__main__":
    run()

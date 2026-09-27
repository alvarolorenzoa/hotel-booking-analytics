"""Cancellation prediction model.

Predicts, at booking time, the probability that a reservation will be cancelled.
Only information available when the booking is made is used as input (no leakage:
reservation_status, assigned_room_type and booking_changes are excluded).

Validation is time-based: the model is trained on past arrivals and tested on the
most recent months, which is how it would be used in production.

Usage (after the pipeline):
    python -m src.model
"""
import json
import logging

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,  # noqa: E402
                             recall_score, roc_auc_score, roc_curve)
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler  # noqa: E402

from src import config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("model")
logging.getLogger("matplotlib").setLevel(logging.WARNING)

TEST_FROM = "2017-03-01"   # train on arrivals before this date, test on arrivals from it
TOP_COUNTRIES = 15
SEED = 42

NUMERIC = ["lead_time", "arrival_month", "arrival_week", "stays_in_weekend_nights", "stays_in_week_nights",
           "adults", "children", "babies", "is_repeated_guest", "previous_cancellations",
           "previous_bookings_not_canceled", "days_in_waiting_list", "adr", "required_car_parking_spaces",
           "total_of_special_requests", "has_agent", "has_company"]
CATEGORICAL = ["hotel", "meal", "market_segment", "distribution_channel", "reserved_room_type",
               "deposit_type", "customer_type", "country_group"]

QUERY = """
SELECT f.*, h.hotel_name AS hotel, ch.market_segment, ch.distribution_channel,
       cu.customer_type, cu.is_repeated_guest, co.country_code,
       d.full_date AS arrival_date, d.month AS arrival_month, d.week_of_year AS arrival_week
FROM fact_bookings f
JOIN dim_hotel h    USING (hotel_key)
JOIN dim_channel ch USING (channel_key)
JOIN dim_customer cu USING (customer_key)
JOIN dim_country co USING (country_key)
JOIN dim_date d     ON d.date_key = f.arrival_date_key
"""


def load_dataset() -> pd.DataFrame:
    con = duckdb.connect(str(config.DB_FILE), read_only=True)
    df = con.execute(QUERY).df()
    con.close()
    top = df["country_code"].value_counts().head(TOP_COUNTRIES).index
    df["country_group"] = df["country_code"].where(df["country_code"].isin(top), "OTHER")
    return df


def build_models() -> dict[str, Pipeline]:
    linear_prep = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=20), CATEGORICAL),
    ])
    tree_prep = ColumnTransformer([
        ("num", "passthrough", NUMERIC),
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CATEGORICAL),
    ])
    n_num = len(NUMERIC)
    cat_mask = [False] * n_num + [True] * len(CATEGORICAL)
    return {
        "Logistic Regression (baseline)": Pipeline([
            ("prep", linear_prep), ("clf", LogisticRegression(max_iter=2000, C=1.0))]),
        "Gradient Boosting": Pipeline([
            ("prep", tree_prep),
            ("clf", HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=48,
                                                   categorical_features=cat_mask, random_state=SEED))]),
    }


def evaluate(y_true, proba, threshold=0.5) -> dict:
    pred = (proba >= threshold).astype(int)
    return {
        "roc_auc": round(roc_auc_score(y_true, proba), 3),
        "accuracy": round(accuracy_score(y_true, pred), 3),
        "precision": round(precision_score(y_true, pred), 3),
        "recall": round(recall_score(y_true, pred), 3),
        "f1": round(f1_score(y_true, pred), 3),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
    }


def logistic_drivers(model: Pipeline, top: int = 12) -> pd.DataFrame:
    """Largest standardized coefficients of the logistic regression = main cancellation drivers."""
    names = model.named_steps["prep"].get_feature_names_out()
    coefs = model.named_steps["clf"].coef_[0]
    labels = [n.split("__", 1)[1].replace("infrequent_sklearn", "other (infrequent)") for n in names]
    df = pd.DataFrame({"feature": labels, "coef": coefs})
    df["odds_ratio"] = np.exp(df["coef"]).round(2)
    return df.reindex(df["coef"].abs().sort_values(ascending=False).index).head(top)


def run() -> None:
    df = load_dataset()
    train = df[df["arrival_date"] < pd.Timestamp(TEST_FROM)]
    test = df[df["arrival_date"] >= pd.Timestamp(TEST_FROM)]
    X_cols = NUMERIC + CATEGORICAL
    log.info("Train: %s bookings (to %s) | Test: %s bookings (from %s)",
             f"{len(train):,}", TEST_FROM, f"{len(test):,}", TEST_FROM)

    results, probas = {}, {}
    for name, model in build_models().items():
        model.fit(train[X_cols], train["is_canceled"])
        proba = model.predict_proba(test[X_cols])[:, 1]
        probas[name] = proba
        results[name] = evaluate(test["is_canceled"], proba)
        log.info("%-32s AUC %.3f | F1 %.3f", name, results[name]["roc_auc"], results[name]["f1"])
        if name.startswith("Logistic"):
            drivers = logistic_drivers(model)

    # Business view: how much of the revenue that was later cancelled is flagged as high risk?
    best = max(results, key=lambda k: results[k]["roc_auc"])
    flagged = probas[best] >= 0.5
    at_risk_total = test["lost_revenue"].sum()
    at_risk_caught = test.loc[flagged, "lost_revenue"].sum()
    business = {
        "best_model": best,
        "test_cancellation_rate_pct": round(100 * test["is_canceled"].mean(), 1),
        "lost_revenue_in_test_eur": round(float(at_risk_total), 0),
        "lost_revenue_flagged_eur": round(float(at_risk_caught), 0),
        "lost_revenue_flagged_pct": round(100 * at_risk_caught / at_risk_total, 1),
    }

    out = {"train_rows": len(train), "test_rows": len(test), "test_from": TEST_FROM,
           "models": results, "business": business,
           "logistic_drivers": drivers[["feature", "coef", "odds_ratio"]].round(3).to_dict("records")}
    (config.DOCS_DIR / "model_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    write_report(out)
    plot_roc(test["is_canceled"], probas)
    plot_drivers(drivers)
    log.info("Best model: %s | flags %.1f%% of the revenue later lost to cancellations",
             best, business["lost_revenue_flagged_pct"])


def write_report(out: dict) -> None:
    lines = ["# Cancellation Model Report", "", "_Generated automatically by `src/model.py`._", "",
             f"- Time-based split: train on arrivals before **{out['test_from']}** "
             f"({out['train_rows']:,} bookings), test on arrivals from that date ({out['test_rows']:,}).",
             "- Only features known at booking time are used (no data leakage).", "",
             "| Model | ROC AUC | Accuracy | Precision | Recall | F1 |", "|---|---:|---:|---:|---:|---:|"]
    for name, m in out["models"].items():
        lines.append(f"| {name} | {m['roc_auc']} | {m['accuracy']} | {m['precision']} | {m['recall']} | {m['f1']} |")
    b = out["business"]
    lines += ["", "## Business impact", "",
              f"In the test period {b['test_cancellation_rate_pct']}% of bookings were cancelled, "
              f"worth **{b['lost_revenue_in_test_eur']:,.0f} €**. The {b['best_model']} flags as high-risk "
              f"the bookings behind **{b['lost_revenue_flagged_pct']}%** of that lost revenue "
              f"({b['lost_revenue_flagged_eur']:,.0f} €), so revenue management can act before the stay "
              "(deposit policy, reminders, controlled overbooking).", "",
              "## Main cancellation drivers (logistic regression)", "",
              "Odds ratio > 1 increases the probability of cancellation; < 1 reduces it. "
              "Numeric features are standardized (effect of +1 standard deviation).", "",
              "| Feature | Coefficient | Odds ratio |", "|---|---:|---:|"]
    for d in out["logistic_drivers"]:
        odds = "< 0.01" if d["odds_ratio"] < 0.01 else d["odds_ratio"]
        lines.append(f"| {d['feature']} | {d['coef']} | {odds} |")
    lines += ["", "![ROC curve](img/roc_curve.png)", "", "![Drivers](img/cancellation_drivers.png)"]
    (config.DOCS_DIR / "model_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_roc(y, probas: dict) -> None:
    fig, ax = plt.subplots(figsize=(5, 4.2), dpi=120)
    for (name, p), color in zip(probas.items(), ["#9AA5B1", "#1F3864"]):
        fpr, tpr, _ = roc_curve(y, p)
        ax.plot(fpr, tpr, color=color, lw=2, label=f"{name} (AUC {roc_auc_score(y, p):.2f})")
    ax.plot([0, 1], [0, 1], ls="--", color="#cccccc")
    ax.set(title="ROC curve – test period", xlabel="False positive rate", ylabel="True positive rate")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(config.IMG_DIR / "roc_curve.png")
    plt.close(fig)


def plot_drivers(drivers: pd.DataFrame) -> None:
    d = drivers.iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=120)
    ax.barh(d["feature"], d["coef"], color=np.where(d["coef"] > 0, "#E07A1F", "#1F3864"))
    ax.axvline(0, color="#666666", lw=0.8)
    ax.set(title="Cancellation drivers (logistic regression)", xlabel="Coefficient (+ = more cancellations)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(config.IMG_DIR / "cancellation_drivers.png")
    plt.close(fig)


if __name__ == "__main__":
    run()

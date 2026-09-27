#!/usr/bin/env bash
# Runs the full project: ETL pipeline -> business SQL analysis -> cancellation model -> tests
set -euo pipefail
cd "$(dirname "$0")"

python -m src.pipeline
python -m src.analysis
python -m src.model
python -m pytest -q
echo "Done. Outputs: data/processed/*.parquet (Power BI) and docs/ (reports + charts)."

# Data Quality Report

_Generated automatically by `src/pipeline.py`._

## 1. Raw data profile

- Rows: **119,390** · Columns: **32**
- Fully duplicated rows: **31,994** (kept: the source has no booking ID, so identical rows are treated as separate bookings, e.g. group reservations)

| Column | Missing values | % |
|---|---:|---:|
| children | 4 | 0.0 % |
| country | 488 | 0.41 % |
| agent | 16,340 | 13.69 % |
| company | 112,593 | 94.31 % |

**Outliers (IQR rule) in key numeric columns**

| Column | Outliers |
|---|---:|
| adr | 3,793 |
| lead_time | 3,005 |
| stays_in_week_nights | 3,354 |
| days_in_waiting_list | 3,698 |

ADR (average daily rate, €): min **-6.38**, median **94.58**, max **5400.0**

## 2. Cleaning actions

| Rule | Rows removed |
|---|---:|
| Bookings with zero guests | 180 |
| Negative ADR | 1 |
| ADR above 1000 € (data-entry error) | 1 |

Imputations: `children` → 0, `country` → `UNK`, `meal` 'Undefined' → 'SC' (same meaning in the source). `agent` / `company` nulls mean *no agent / no company* and are kept as flags.

## 3. Validation of the clean table

Rows after cleaning: **119,208**

- ✅ row count >= 100,000
- ✅ booking_id is unique
- ✅ no nulls in key columns
- ✅ adr within [0, MAX_VALID_ADR]
- ✅ every booking has at least one guest
- ✅ lead_time is non-negative
- ✅ is_canceled is binary
- ✅ revenue is zero for cancelled bookings
- ✅ total_nights = weekend + week nights

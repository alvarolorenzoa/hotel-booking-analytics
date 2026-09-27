# Business Insights

_Generated automatically by `src/analysis.py` from `sql/02_business_queries.sql`._

## Kpis by hotel

| hotel | bookings | cancellation_rate_pct | realised_revenue_m | lost_revenue_m | avg_adr | avg_nights | avg_lead_time_days |
|---|---|---|---|---|---|---|---|
| City Hotel | 79,162 | 41.8 | 14.39 | 10.88 | 106.04 | 2.92 | 110.0 |
| Resort Hotel | 40,046 | 27.8 | 11.6 | 5.84 | 90.83 | 4.14 | 93.0 |

## Cancellation by lead time

| lead_time_bucket | bookings | cancellation_rate_pct |
|---|---|---|
| 0-7 days | 19,635 | 9.6 |
| 8-30 days | 18,945 | 27.9 |
| 31-90 days | 29,528 | 37.7 |
| 91-180 days | 26,420 | 44.7 |
| 181-365 days | 21,533 | 55.5 |
| 365+ days | 3,147 | 67.7 |

## Cancellation by deposit

| deposit_type | bookings | cancellation_rate_pct | avg_lead_time_days |
|---|---|---|---|
| No Deposit | 104,460 | 28.4 | 89.0 |
| Non Refund | 14,586 | 99.4 | 213.0 |
| Refundable | 162 | 22.2 | 152.0 |

## Segment performance

| market_segment | bookings | share_of_bookings_pct | cancellation_rate_pct | avg_adr | revenue_k | revenue_rank |
|---|---|---|---|---|---|---|
| Online TA | 56,408 | 47.3 | 36.8 | 114.04 | 13,707 | 1 |
| Offline TA/TO | 24,181 | 20.3 | 34.3 | 83.55 | 5,659 | 2 |
| Direct | 12,582 | 10.6 | 15.4 | 114.1 | 4,098 | 3 |
| Groups | 19,790 | 16.6 | 61.1 | 77.31 | 1,869 | 4 |
| Corporate | 5,282 | 4.4 | 18.8 | 67.29 | 578.0 | 5 |
| Aviation | 235 | 0.2 | 22.1 | 100.57 | 71.0 | 6 |
| Complementary | 728 | 0.6 | 12.2 | 3.11 | 5.0 | 7 |
| Undefined | 2 | 0.0 | 100.0 |  | 0.0 | 8 |

## Top countries pareto

| country_name | bookings | cancellation_rate_pct | revenue_k | revenue_share_pct | cumulative_share_pct |
|---|---|---|---|---|---|
| Portugal | 48,482 | 56.7 | 5,540 | 21.3 | 21.3 |
| United Kingdom | 12,119 | 20.2 | 4,111 | 15.8 | 37.1 |
| France | 10,401 | 18.6 | 3,098 | 11.9 | 49.1 |
| Spain | 8,560 | 25.4 | 2,246 | 8.6 | 57.7 |
| Germany | 7,285 | 16.7 | 2,068 | 8.0 | 65.7 |
| Ireland | 3,374 | 24.7 | 1,240 | 4.8 | 70.4 |
| Italy | 3,761 | 35.4 | 866.0 | 3.3 | 73.8 |
| Belgium | 2,342 | 20.2 | 759.0 | 2.9 | 76.7 |
| Netherlands | 2,103 | 18.4 | 632.0 | 2.4 | 79.1 |
| Switzerland | 1,726 | 24.8 | 548.0 | 2.1 | 81.2 |

## Seasonality adr

| month | month_name | city_adr | resort_adr |
|---|---|---|---|
| 1 | Jan | 82.33 | 48.76 |
| 2 | Feb | 86.52 | 54.15 |
| 3 | Mar | 90.66 | 57.08 |
| 4 | Apr | 111.96 | 75.87 |
| 5 | May | 120.67 | 76.66 |
| 6 | Jun | 117.87 | 107.97 |
| 7 | Jul | 115.82 | 150.12 |
| 8 | Aug | 118.67 | 181.21 |
| 9 | Sep | 112.78 | 96.42 |
| 10 | Oct | 102.0 | 61.78 |
| 11 | Nov | 86.95 | 48.71 |
| 12 | Dec | 88.4 | 68.41 |

## Monthly revenue yoy

| year_month | revenue_k | revenue_prev_year_k | yoy_growth_pct |
|---|---|---|---|
| 2015-07 | 758.0 |  |  |
| 2015-08 | 1,138 |  |  |
| 2015-09 | 1,055 |  |  |
| 2015-10 | 785.0 |  |  |
| 2015-11 | 347.0 |  |  |
| 2015-12 | 430.0 |  |  |
| 2016-01 | 265.0 |  |  |
| 2016-02 | 484.0 |  |  |
| 2016-03 | 767.0 |  |  |
| 2016-04 | 896.0 |  |  |
| 2016-05 | 1,073 |  |  |
| 2016-06 | 1,145 |  |  |
| 2016-07 | 1,524 | 758.0 | 101.0 |
| 2016-08 | 1,808 | 1,138 | 58.9 |
| 2016-09 | 1,289 | 1,055 | 22.2 |
| 2016-10 | 1,072 | 785.0 | 36.6 |
| 2016-11 | 687.0 | 347.0 | 98.2 |
| 2016-12 | 658.0 | 430.0 | 53.1 |
| 2017-01 | 512.0 | 265.0 | 93.5 |
| 2017-02 | 663.0 | 484.0 | 37.0 |
| 2017-03 | 884.0 | 767.0 | 15.3 |
| 2017-04 | 1,203 | 896.0 | 34.3 |
| 2017-05 | 1,322 | 1,073 | 23.2 |
| 2017-06 | 1,438 | 1,145 | 25.6 |
| 2017-07 | 1,817 | 1,524 | 19.2 |
| 2017-08 | 1,970 | 1,808 | 9.0 |

## Repeat vs new

| guest_status | bookings | cancellation_rate_pct | avg_adr | avg_special_requests |
|---|---|---|---|---|
| New guest | 115,454 | 37.8 | 101.79 | 0.57 |
| Repeat guest | 3,754 | 14.7 | 63.91 | 0.63 |

## Special requests effect

| special_requests | bookings | cancellation_rate_pct |
|---|---|---|
| 0 | 70,199 | 47.8 |
| 1 | 33,183 | 22.0 |
| 2 | 12,952 | 22.1 |
| 3 | 2,874 | 16.8 |

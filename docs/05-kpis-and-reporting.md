# KPIs and Reporting

A KPI without a written definition becomes two KPIs within a quarter. Each one
below states its formula, its grain, its source table, and its exclusions.

---

## 1. KPI definitions

### Pooling rate
*Share of trips that shared a vehicle.* New — now that pooling is live.

```
pooling_rate = trips with ≥2 attached bookings ÷ all closed trips
```

- **Grain:** period × product line
- **Source:** `Trip` ⋈ `BookingRequest`
- **Excludes:** cancelled trips, standby-only trips
- **Note:** attribution for a pooled trip counts the trip once, not once per
  product line. The per-product-line view answers "how often did *my* bookings
  join a pool", which is a different question — report both, labelled.

### Average occupancy
```
occupancy = Σ seats_used ÷ Σ seats_dispatched
```
- **Grain:** period × vehicle class
- **Excludes:** cargo-only trips (`passenger_count = 0`), standby days

### Booking lead time
*The leading indicator for call-outs.*
```
lead_time_hours = requested_departure − submitted_at   (frozen at submit)
```
- **Grain:** period × product line
- Report the **median and the 10th percentile**, not the mean. The mean hides
  the tail, and the tail is where call-outs live.

### Call-out rate and cost
```
call_out_rate = bookings with is_call_out ÷ all submitted bookings
call_out_cost = Σ TripCost where cost_type = CALL_OUT_PREMIUM
```
- **Baseline:** 35 trips, $10,269 — the largest exception on the current
  scorecard
- Always report alongside the **reason-code breakdown**. The rate says there is
  a problem; the reason codes say whose.

### Owned-vs-rental assignment ratio
```
owned_ratio = trips assigned to OWNED vehicles ÷ all assigned trips
```
- **Baseline:** owned vehicles run at ~46% utilisation while rentals are hired
  alongside them
- Report with the **override-reason breakdown**. A dispatcher choosing rental
  because no owned unit was field-capable is a fleet composition problem; doing
  it out of habit is a training problem. The ratio alone cannot tell them apart.

### Right-sizing rate
```
right_sizing_rate = trips where assigned class rank = minimum sufficient rank
                    ÷ all assigned trips
```
- Minimum sufficient rank = lowest `VehicleClass.rank` satisfying passengers,
  cargo weight, and field capability

### Data completeness
```
completeness = trips closed with odometer AND destination ÷ all closed trips
```
- **Target: 100%, permanently.** Once TRB-044 ships this is structurally 100%;
  the KPI exists to detect a regression — a new write path, a data fix script, a
  dropped constraint. Alert on any value below 100%.
- **Baseline before the app:** 126 blank-mileage rows, 27 blank destinations

### Utilisation
```
utilisation = VehicleDays where is_utilised ÷ VehicleDays in scope
```
- `is_utilised` is true for `ON_TRIP` and `FIELD_STANDBY`
- **Excludes** `DISPOSED` days entirely — this is what makes the 6x6 and the 5T
  disappear without a manual exclusion list

### Contract-basis utilisation
*The number for rate negotiations.*
```
contract_utilisation = days used ÷ days paid for
```
- **Grain:** contract × unit × period
- Days paid comes from the contract period; days used from `VehicleDay`
- **Baseline:** 35 rental units, $40,553/month

### Non-revenue share
```
non_revenue_share = trips whose bookings are all NON_REVENUE ÷ all closed trips
```
- **Baseline: 37.8%.** This is the pool the pooling engine is aimed at, so it is
  read together with pooling rate — non-revenue share falling *because* pooling
  rose is the win; falling for any other reason needs explaining.

### Cost per km
```
cost_per_km = Σ TripCost.amount ÷ Σ Trip.distance_km
```
- **Grain:** vehicle, class, product line, period
- **Excludes** trips with `distance_km = 0` (standby) from the denominator —
  and, necessarily, from the numerator too, or standby cost silently inflates
  every other vehicle's rate

---

## 2. Power BI semantic model

**Architecture:** application database → Power BI direct connection. The Excel
consolidation step disappears entirely.

Power BI reads **versioned read-only views**, never base tables, so schema
refactors do not break the semantic model.

### Dimensions

| View | Grain | Key |
|---|---|---|
| `bi_dim_date` | day | `date_key` |
| `bi_dim_vehicle` | vehicle | `plate` |
| `bi_dim_location` | location | `location_code` |
| `bi_dim_product_line` | product line | `product_line_code` |
| `bi_dim_contract` | contract | `contract_ref` |
| `bi_dim_vehicle_class` | class | `class_code` |

### Facts

| View | Grain | Notes |
|---|---|---|
| `bi_fact_trip` | one row per trip | Distance, hours, occupancy, pooled flag, destination class |
| `bi_fact_booking` | one row per booking | Lead time, call-out flag, reason code, revenue class |
| `bi_fact_cost` | one row per cost line | The only cost source; joins to product line for chargeback |
| `bi_fact_vehicle_day` | vehicle × day | Utilisation, including field standby |

`bi_fact_vehicle_day` is what makes utilisation consistent between the app and
the dashboard. Both count rows in the same table; there is no second definition
to drift.

### Model rules

- Star schema; no snowflaking beyond `vehicle → class`
- Single direction filters from dimension to fact
- All measures defined in DAX in one measures table, matching §1 formulas
- Every view carries `_period_status` so open-period figures are visibly
  provisional

---

## 3. Reconciliation design

This is what Finance will ask for.

**1 · Period lock.** Once a month is closed, freeze the data. Late entries post
to the next period, exactly as the GL works.

**2 · Allocated vs invoiced.** Trip-level allocated cost on one side, rental and
fuel invoices on the other, with the variance explained.

**3 · Reconciliation report.** Total transport cost in the app versus the GL
account balance, per cost centre, per month, with a documented variance bridge:

```
Allocated cost (app)                              84,210
  + trips closed after period close                    0   ← period lock working
  + invoices received, not yet allocated             1,240
  − allocated to trips awaiting invoice             (2,105)  ← accrual
  ± rate differences (contract vs applied)             310
  ± cost centre mapping differences                     0   ← must stay zero
= GL balance                                      83,655
Variance                                             555   (0.66%)
```

The mapping-differences line is the diagnostic. If it is ever non-zero, the
cost-centre mapping is wrong and no other line should be investigated first.

**4 · Accrual support.** At month end the app produces the accrual figure for
trips taken but not yet invoiced.

**5 · Audit trail.** Every cost line traceable to a trip, a vehicle, and a
requester.

**Target: variance under 2%.** Anything wider means the cost-centre mapping is
wrong, and it is better to find that in month one than in month twelve.

---

## 4. Reporting cadence

| Report | Frequency | Audience |
|---|---|---|
| Dispatcher queue and exceptions | Live | Dispatch |
| Data completeness | Daily | Fleet manager |
| Alerts (idle, utilisation, fuel mismatch) | Push, as triggered | Fleet manager |
| Pooling rate, occupancy, lead time | Weekly | Fleet manager, product lines |
| Call-out root cause | Monthly | Product line managers |
| Chargeback statement | Monthly, at close | Product line managers |
| Reconciliation and accrual | Monthly, at close | Finance |
| Contract utilisation | Quarterly, and pre-renewal | Fleet manager, procurement |
| Fleet sizing | Quarterly | Fleet manager, operations |

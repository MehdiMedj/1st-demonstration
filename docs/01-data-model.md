# Data Model

> Get this right and everything downstream is easy. Get it wrong and you rebuild
> in a year.

Conventions: all money is `DecimalField(max_digits=12, decimal_places=2)` —
never float. All timestamps are `timezone.now`-aware, stored UTC, displayed in
Africa/Algiers. All masters carry `active` rather than being deleted, so history
resolves.

---

## 1. Entity map

```
ProductLine ──┬── BookingRequest ──┐
              │                    │  N..1
RentalContract├── Vehicle ─────────┼── Trip ──┬── TripEvent
              │      │             │          ├── OdometerReading
              │      └─ VehicleStatusHistory  ├── TripCost ── AccountingPeriod
              │      └─ VehicleDay            └── (destination_class snapshot)
VehicleClass ─┘
Location ── LocationAlias
Driver
CallOutReasonCode ── BookingRequest
Invoice ── InvoiceLine ── ReconciliationRun
```

The single most important relationship: **`Trip 1 ── N BookingRequest`**.
See DD-1 in `06-decisions-and-risks.md`.

---

## 2. Master data

### 2.1 `ProductLine`

Cost centre. The single most valuable field in the application.

| Field | Type | Notes |
|---|---|---|
| `code` | `CharField(16)`, **unique** | **Must equal the finance chart-of-accounts code** |
| `name` | `CharField(120)` | |
| `gl_account` | `CharField(32)` | Target GL account for transport cost |
| `manager` | `FK(User, null)` | Receives chargeback reports and approval escalations |
| `is_revenue_generating` | `BooleanField` | Default for requests; overridable per booking |
| `active` | `BooleanField` | |

Twenty-one product lines appear in current fleet data. The mapping is agreed
with Finance **before build**, not after.

### 2.2 `Location`

Kills 316 free-text spellings and makes the rig-site rule automatic.

| Field | Type | Notes |
|---|---|---|
| `code` | `CharField(24)`, **unique** | e.g. `ENF-62`, `BASE-02` |
| `name` | `CharField(160)` | |
| `location_type` | choices | `BASE`, `RIG_SITE`, `AIRPORT`, `CLIENT_FACILITY`, `WORKSHOP`, `OTHER` |
| `classification` | choices | `BASE` \| `FIELD` — **explicit, not derived**, so exceptions are expressible |
| `latitude`, `longitude` | `DecimalField(9,6)` | Required for geofencing and distance estimation |
| `geofence_radius_m` | `PositiveIntegerField` | Default 500; rig sites typically wider |
| `active` | `BooleanField` | |

`classification` is what makes field standby native rather than a keyword list.
`location_type` is descriptive; `classification` is the one costing and
utilisation read.

### 2.3 `LocationAlias`

The migration path for 316 historical spellings, and the landing zone for AI
normalisation.

| Field | Type | Notes |
|---|---|---|
| `location` | `FK(Location)` | |
| `raw_text` | `CharField(255)` | Normalised (case-folded, whitespace-collapsed) |
| `source` | choices | `MIGRATION`, `AI_SUGGESTED`, `MANUAL` |
| `confidence` | `DecimalField(4,3), null` | Populated for `AI_SUGGESTED` only |
| `confirmed_by` | `FK(User, null)` | |
| `confirmed_at` | `DateTimeField(null)` | |

**Constraint:** an alias only resolves inbound text when `confirmed_at` is set.
AI proposes; a human confirms; only then does the mapping take effect.

```sql
CREATE UNIQUE INDEX uniq_alias_confirmed
  ON masters_locationalias (raw_text)
  WHERE confirmed_at IS NOT NULL;
```

### 2.4 `VehicleClass`

Drives right-sizing. "Do not dispatch a 4x4 to carry one passenger to Algiers."

| Field | Type | Notes |
|---|---|---|
| `code`, `name` | | `LIGHT_SEDAN`, `4X4_PICKUP`, `BUS_30`, `TRUCK_5T` … |
| `seats` | `PositiveSmallIntegerField` | Denominator of average occupancy |
| `payload_kg` | `PositiveIntegerField` | |
| `is_field_capable` | `BooleanField` | Required for `FIELD`-classified destinations |
| `rank` | `PositiveSmallIntegerField` | Ascending cost/capability; the optimiser picks the lowest sufficient rank |

### 2.5 `Vehicle`

| Field | Type | Notes |
|---|---|---|
| `plate` | `CharField(20)`, **unique** | **One plate per record, regex-validated** |
| `fleet_number` | `CharField(20)`, unique | Internal identifier |
| `vehicle_class` | `FK(VehicleClass)` | |
| `ownership` | choices | `OWNED` \| `RENTAL` |
| `rental_contract` | `FK(RentalContract, null)` | Required when `ownership=RENTAL` |
| `daily_rate` | `Decimal(12,2)` | Rental day rate, or owned depreciation-equivalent |
| `fuel_consumption_l_per_100km` | `Decimal(6,2)` | With fuel price → deterministic fuel cost |
| `home_base` | `FK(Location)` | Deadhead calculation origin |
| `current_status` | choices | `ACTIVE`, `STANDBY`, `WORKSHOP`, `OFF_HIRE`, `DISPOSED` |
| `odometer_current` | `PositiveIntegerField` | Last confirmed reading; anomaly baseline |
| `acquired_on`, `disposed_on` | `DateField(null)` | |

**The `plate` unique constraint alone prevents the 226 dual-plate rows.** Format
validation is a `RegexValidator` on the field *and* a Postgres `CHECK`, because
data-fix scripts bypass Django validators.

```python
class Vehicle(models.Model):
    plate = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(ALGERIA_PLATE_RE, "One plate, format NNNNN-NNN-NN")],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                # no separator characters => no second plate smuggled in
                check=~models.Q(plate__regex=r"[/,;&+]|\s{2,}"),
                name="vehicle_single_plate",
            ),
            models.CheckConstraint(
                check=~models.Q(ownership="RENTAL") | models.Q(rental_contract__isnull=False),
                name="rental_requires_contract",
            ),
        ]
```

### 2.6 `VehicleStatusHistory`

So decommissioned units — the 6x6, the 5T — leave utilisation automatically
instead of by manual exclusion.

| Field | Type | Notes |
|---|---|---|
| `vehicle` | `FK(Vehicle)` | |
| `status` | choices | Same set as `Vehicle.current_status` |
| `period` | `DateRangeField` | Postgres range; half-open `[from, to)` |
| `reason` | `CharField(255)` | |
| `changed_by` | `FK(User)` | |

**Non-overlap is enforced by the database**, requiring `btree_gist`:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE masters_vehiclestatushistory
  ADD CONSTRAINT vehicle_status_no_overlap
  EXCLUDE USING gist (vehicle_id WITH =, period WITH &&);
```

Utilisation queries read this table, never `Vehicle.current_status`. Current
status is a cache of "the row whose period contains today".

### 2.7 `RentalContract`

Currently 35 units at $40,553/month.

| Field | Type | Notes |
|---|---|---|
| `contract_ref` | `CharField(40)`, unique | |
| `supplier` | `CharField(160)` | |
| `start_date`, `end_date` | `DateField` | |
| `notice_period_days` | `PositiveSmallIntegerField` | Drives the renewal alert lead time |
| `monthly_rate`, `daily_rate` | `Decimal(12,2)` | |
| `unit_count` | `PositiveSmallIntegerField` | |
| `auto_renew` | `BooleanField` | |
| `status` | choices | `ACTIVE`, `NOTICE_GIVEN`, `EXPIRED`, `TERMINATED` |

Contract-basis utilisation = days used ÷ days paid, computed from `VehicleDay`
against the contract period. That is the number for rate negotiations.

### 2.8 `Driver`

| Field | Type | Notes |
|---|---|---|
| `employee_ref` | `CharField(24)`, unique | |
| `user` | `OneToOne(User, null)` | For mobile check-in/out |
| `licence_class`, `licence_expiry` | | Expiry drives an alert |
| `home_base` | `FK(Location)` | |
| `active` | `BooleanField` | |

### 2.9 `CallOutReasonCode`

Reason codes accumulate into a root-cause report — that is what actually reduces
call-outs.

| Field | Type | Notes |
|---|---|---|
| `code`, `label` | | |
| `category` | choices | `RIG_DELAY`, `EQUIPMENT_FAILURE`, `CLIENT_REQUEST`, `PLANNING_MISS`, `WEATHER`, `OTHER` |
| `requires_narrative` | `BooleanField` | `OTHER` forces free text |
| `active` | `BooleanField` | |

---

## 3. Transaction data

### 3.1 `BookingRequest` — the front door

Captures at request time, not afterwards.

| Field | Type | Notes |
|---|---|---|
| `booking_ref` | `CharField(20)`, unique | Generated `BK-YYYYMM-NNNNN` |
| `requester` | `FK(User)` | |
| `product_line` | `FK(ProductLine)` | **Required. No null, no default.** |
| `purpose` | `CharField(255)` | |
| `origin`, `destination` | `FK(Location)` | **Required. Controlled list only — no free text field exists to fall back to.** |
| `requested_departure` | `DateTimeField` | |
| `time_window_minutes` | `PositiveSmallIntegerField` | Flexibility offered; widens pooling matches |
| `expected_duration_minutes` | `PositiveIntegerField` | |
| `passenger_count` | `PositiveSmallIntegerField` | |
| `cargo_description` | `CharField(255)` | |
| `cargo_weight_kg` | `PositiveIntegerField` | Together drive vehicle class |
| `revenue_classification` | choices | `REVENUE` \| `NON_REVENUE` — **declared at booking, never inferred** |
| `suggested_vehicle_class` | `FK(VehicleClass, null)` | System-computed from load |
| `status` | choices | See §4 |
| `is_call_out` | `BooleanField` | **System-set at submit. Not user-editable.** |
| `call_out_reason_code` | `FK(CallOutReasonCode, null)` | Required when `is_call_out` |
| `call_out_justification` | `TextField` | |
| `lead_time_hours` | `Decimal(8,2), null` | Frozen at submit. Leading indicator for call-outs |
| `pooling_offered` | `BooleanField` | Was a pool match shown? |
| `pooling_declined_reason` | `CharField(255)` | **Required if a match was shown and declined** |
| `trip` | `FK(Trip, null, related_name="bookings")` | Assignment target |
| `approved_by`, `approved_at` | | |
| `created_at`, `submitted_at` | | |

Constraints:

```python
constraints = [
    models.CheckConstraint(
        check=~models.Q(is_call_out=True) | models.Q(call_out_reason_code__isnull=False),
        name="callout_requires_reason",
    ),
    models.CheckConstraint(
        check=~models.Q(pooling_offered=True, trip__isnull=True)
              | ~models.Q(pooling_declined_reason=""),
        name="pool_decline_requires_reason",
    ),
]
```

### 3.2 `Trip` — one physical vehicle movement

| Field | Type | Notes |
|---|---|---|
| `trip_id` | `CharField(20)`, unique | `TR-YYYYMM-NNNNN` |
| `vehicle` | `FK(Vehicle)` | |
| `driver` | `FK(Driver)` | |
| `origin`, `destination` | `FK(Location)` | |
| `destination_class` | choices | `BASE` \| `FIELD` — **snapshot at closure**, so later master edits do not restate history |
| `planned_departure`, `planned_arrival` | `DateTimeField` | |
| `actual_departure`, `actual_arrival` | `DateTimeField(null)` | |
| `odometer_start`, `odometer_end` | `PositiveIntegerField(null)` | **Both required to close** |
| `distance_km` | `PositiveIntegerField(null)` | Stored `end - start`, not computed at read time |
| `planned_km` | `PositiveIntegerField(null)` | From location coordinates; feeds the fuel-vs-distance anomaly rule |
| `seats_dispatched` | `PositiveSmallIntegerField` | `vehicle.vehicle_class.seats` at dispatch |
| `seats_used` | `PositiveSmallIntegerField` | Σ passengers over attached bookings |
| `status` | choices | See §4 |
| `accounting_period` | `FK(AccountingPeriod, null)` | Set at closure — determines which period the cost lands in |
| `is_standby` | `BooleanField` | Trip represents field standby, not a movement |

**`is_pooled` is not stored.** It is `bookings.count() > 1`, exposed as a
property and as a Postgres view column for Power BI. Storing it invites drift.

The closure gate, in the database:

```python
models.CheckConstraint(
    check=~models.Q(status__in=["CLOSED", "COSTED", "LOCKED"]) | models.Q(
        odometer_start__isnull=False,
        odometer_end__isnull=False,
        destination__isnull=False,
    ),
    name="closed_trip_requires_odometer_and_destination",
)
models.CheckConstraint(
    check=models.Q(odometer_end__gte=models.F("odometer_start")),
    name="odometer_not_decreasing",
)
```

This is the constraint that eliminates the 126 blank-mileage and 27
blank-destination rows. It is stated once, in the schema, and every write path
inherits it.

### 3.3 `TripEvent`

Audit trail for check-in/out and geofence crossings.

| Field | Type | Notes |
|---|---|---|
| `trip` | `FK(Trip)` | |
| `event_type` | choices | `CHECK_IN`, `DEPART`, `GEOFENCE_ENTER`, `GEOFENCE_EXIT`, `ARRIVE`, `CHECK_OUT`, `STANDBY_START`, `STANDBY_END` |
| `occurred_at` | `DateTimeField` | Device time |
| `recorded_at` | `DateTimeField` | Server receipt — differs when offline-queued |
| `latitude`, `longitude` | `Decimal(9,6), null` | |
| `location` | `FK(Location, null)` | Resolved by geofence |
| `source` | choices | `MOBILE`, `TELEMATICS`, `MANUAL` |
| `created_by` | `FK(User, null)` | Null for telematics |

Append-only. No updates, no deletes.

### 3.4 `OdometerReading`

**Odometer photo or telematics feed, not typed.**

| Field | Type | Notes |
|---|---|---|
| `trip` | `FK(Trip)` | |
| `reading_type` | choices | `START` \| `END` |
| `value_km` | `PositiveIntegerField` | **The authoritative value** |
| `capture_method` | choices | `PHOTO_OCR`, `TELEMATICS`, `MANUAL` |
| `photo` | `ImageField(null)` | Required when `capture_method=PHOTO_OCR` |
| `ocr_value` | `PositiveIntegerField(null)` | What the model read |
| `ocr_confidence` | `Decimal(4,3), null` | |
| `confirmed_by` | `FK(User, null)` | |
| `manual_override_reason` | `CharField(255)` | Required when `capture_method=MANUAL` |

The OCR value is a *suggestion*. `value_km` is what a human confirmed or what
telematics reported. Cost is computed from `value_km`. This keeps AI out of the
number that lands in the P&L while still removing the typing.

### 3.5 `VehicleDay` — the utilisation grain

**Rig-site standby is a status, not a gap.** The dashboard applies this as a
manual rule today; this table records it natively.

| Field | Type | Notes |
|---|---|---|
| `vehicle` | `FK(Vehicle)` | |
| `date` | `DateField` | `unique_together(vehicle, date)` |
| `state` | choices | `ON_TRIP`, `FIELD_STANDBY`, `BASE_IDLE`, `WORKSHOP`, `OFF_HIRE`, `DISPOSED` |
| `location` | `FK(Location, null)` | Where it spent the day |
| `km_driven` | `PositiveIntegerField` | Zero is valid and expected for `FIELD_STANDBY` |
| `is_utilised` | `BooleanField` | `state in (ON_TRIP, FIELD_STANDBY)` |
| `trip_count` | `PositiveSmallIntegerField` | |
| `built_at` | `DateTimeField` | Provenance of the nightly build |

Built nightly by Celery from `Trip`, `TripEvent` geofence positions, and
`VehicleStatusHistory`. Rebuildable and idempotent for any date range — never
hand-edited.

Utilisation then becomes trivial and consistent everywhere:

```sql
SELECT vehicle_id,
       COUNT(*) FILTER (WHERE is_utilised)::decimal / COUNT(*) AS utilisation
FROM utilisation_vehicleday
WHERE date BETWEEN %s AND %s AND state <> 'DISPOSED'
GROUP BY vehicle_id;
```

Owned vehicles currently run at ~46% utilisation while rentals are hired
alongside them. This table is how that claim becomes auditable rather than
asserted.

---

## 4. State machines

**BookingRequest**

```
DRAFT ──▶ SUBMITTED ──▶ PENDING_APPROVAL ──▶ APPROVED ──▶ ASSIGNED ──▶ IN_PROGRESS ──▶ COMPLETED
   │           │                │                 │            │
   └──▶ CANCELLED ◀─────────────┴──▶ REJECTED ◀───┘            └──▶ CANCELLED
```

`PENDING_APPROVAL` is entered only when `is_call_out` or when the request
exceeds a product-line threshold. Everything else goes straight to `APPROVED`.
Friction is spent where it changes behaviour, not everywhere.

**Trip**

```
PLANNED ──▶ DISPATCHED ──▶ IN_PROGRESS ──▶ ARRIVED ──▶ CLOSED ──▶ COSTED ──▶ LOCKED
   │             │              │
   └──▶ CANCELLED ◀─────────────┘
```

- `CLOSED` requires odometer start, odometer end, and destination.
- `COSTED` is set by the costing engine; cost lines exist and are immutable.
- `LOCKED` follows period close. No transition out. Corrections post to the next
  open period as adjustments.

Transitions are guarded in a service layer (`dispatch/services.py`), not in
model `save()` overrides, so the legal set is readable in one place.

---

## 5. Costing — deterministic by construction

### 5.1 `CostAllocationRule`

| Field | Type | Notes |
|---|---|---|
| `cost_type` | choices | `RENTAL_SHARE`, `FUEL`, `CALL_OUT_PREMIUM`, `DRIVER`, `TOLL`, `OTHER` |
| `method` | choices | `PER_KM`, `PER_DAY`, `PER_TRIP`, `PCT_OF_BASE`, `PER_PASSENGER_KM` |
| `rate` | `Decimal(12,4)` | |
| `effective_from`, `effective_to` | `DateField` | Non-overlapping per `cost_type` (exclusion constraint) |
| `version` | `PositiveIntegerField` | Stamped onto every cost line it produces |

Rules are versioned and dated. Recomputing a closed period with today's rates is
therefore impossible by construction — the engine selects the rule effective on
the trip date.

### 5.2 `TripCost`

Every trip carries its cost: rental share + fuel + call-out premium.

| Field | Type | Notes |
|---|---|---|
| `trip` | `FK(Trip)` | |
| `cost_type` | choices | As above |
| `product_line` | `FK(ProductLine)` | Allocation target — from the attached booking |
| `booking` | `FK(BookingRequest, null)` | Set when the cost splits across a pooled trip |
| `amount` | `Decimal(12,2)` | |
| `quantity`, `rate_used` | `Decimal(12,4)` | `amount = quantity × rate_used`, reproducible |
| `allocation_basis` | `CharField(255)` | Human-readable: "42% of 310 km, 3 of 7 passengers" |
| `rule_version` | `PositiveIntegerField` | Which rule set produced it |
| `source` | choices | `CALCULATED`, `INVOICE`, `ADJUSTMENT` |
| `accounting_period` | `FK(AccountingPeriod)` | |
| `is_locked` | `BooleanField` | Set at period close; blocks update and delete |

**Pooled-trip allocation** is the one genuinely contentious calculation. Default
method: passenger-km share. A 3-passenger booking on a 7-passenger, 310 km trip
carries 3/7 of the rental share and 3/7 of the fuel. Call-out premium is *not*
shared — it is charged wholly to the product line whose late request caused it.
This must be agreed with Finance before go-live (OQ-2).

### 5.3 `AccountingPeriod`

| Field | Type | Notes |
|---|---|---|
| `year`, `month` | `PositiveSmallIntegerField` | `unique_together` |
| `status` | choices | `OPEN`, `CLOSED`, `LOCKED` |
| `closed_by`, `closed_at` | | |

Once a month is closed the data freezes; late entries post to the next open
period, exactly as the GL works. Enforced by a `BEFORE UPDATE OR DELETE` trigger
on `TripCost`, not only by application code.

### 5.4 `Invoice` / `InvoiceLine` / `ReconciliationRun`

| `ReconciliationRun` field | Notes |
|---|---|
| `period`, `product_line` | Grain of the comparison |
| `allocated_total` | Σ `TripCost.amount` |
| `invoiced_total` | Σ `InvoiceLine.amount` |
| `gl_total` | Imported GL balance |
| `variance_amount`, `variance_pct` | |
| `bridge_notes` | The documented variance bridge Finance will ask for |
| `accrual_amount` | Trips taken but not yet invoiced |

**Target: variance under 2%.** Anything wider means the cost-centre mapping is
wrong, and it is better to find that in month one.

---

## 6. Alerts

`Alert` — `rule_code`, `severity`, `subject_type`, `subject_id`, `triggered_at`,
`resolved_at`, `payload (JSONB)`, `acknowledged_by`.

| Rule | Trigger |
|---|---|
| `IDLE_AT_BASE` | `BASE_IDLE` for more than *N* consecutive `VehicleDay` rows |
| `LOW_UTILISATION` | Rolling 30-day utilisation below threshold |
| `COST_PER_KM_HIGH` | Vehicle or class above target |
| `FUEL_DISTANCE_MISMATCH` | Fuel drawn inconsistent with `distance_km` |
| `CONTRACT_RENEWAL` | `end_date - notice_period_days` reached |
| `ODOMETER_IMPLAUSIBLE` | Jump beyond class-plausible daily maximum |
| `DATA_COMPLETENESS` | Any trip open past *N* hours after planned arrival |

Push, don't wait to be asked.

---

## 7. Indexes

| Table | Index | Serves |
|---|---|---|
| `Trip` | `(vehicle_id, planned_departure)` | Dispatch conflict check |
| `Trip` | `(origin_id, destination_id, planned_departure)` | Pooling corridor match |
| `Trip` | `(accounting_period_id, status)` | Period close |
| `BookingRequest` | `(product_line_id, submitted_at)` | Chargeback reporting |
| `BookingRequest` | `(status, requested_departure)` | Dispatcher queue |
| `VehicleDay` | `(date, state)` | Utilisation aggregates |
| `TripCost` | `(accounting_period_id, product_line_id)` | Reconciliation |
| `TripEvent` | `(trip_id, occurred_at)` | Closure reconstruction |

Power BI reads a set of read-only views (`bi_trip_fact`, `bi_vehicle_dim`,
`bi_location_dim`, `bi_productline_dim`, `bi_cost_fact`) rather than base
tables, so schema refactors do not break the semantic model.

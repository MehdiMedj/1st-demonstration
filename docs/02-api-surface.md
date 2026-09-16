# API Surface

Django REST Framework. Base path `/api/v1/`. JSON only. Token auth for mobile,
session auth for the web app, service accounts for telematics and Power BI.

All list endpoints paginate (`?page`, `?page_size`, max 200) and support
`?ordering=`. All write endpoints return the full updated resource.

---

## 1. Masters

Master data is maintained primarily through Django admin. These endpoints exist
because the booking screens and the mobile app need to read them, and because
integrations need to write them.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/locations/` | `?classification=FIELD&active=true&q=` — typeahead source for origin/destination |
| `GET` | `/locations/{code}/` | |
| `POST` | `/locations/` | Admin role only |
| `GET` | `/locations/resolve/?text=` | Alias lookup. Returns a confirmed match, or `suggestions[]` with confidence and `confirmed: false` |
| `POST` | `/locations/aliases/{id}/confirm/` | Promotes an AI suggestion to an active alias. **Admin role only** |
| `GET` | `/vehicles/` | `?ownership=&status=&class=&available_at=` |
| `GET` | `/vehicles/{plate}/` | Includes current status, contract, rolling utilisation |
| `PATCH` | `/vehicles/{plate}/status/` | Body `{status, effective_from, reason}` — appends to status history, never mutates in place |
| `GET` | `/vehicle-classes/` | |
| `GET` | `/product-lines/` | `?active=true` |
| `GET` | `/drivers/` | `?active=true&base=` |
| `GET` | `/contracts/` | `?status=&expiring_before=` |
| `GET` | `/call-out-reasons/` | |

---

## 2. Booking

### `POST /bookings/`

Creates a `DRAFT`. All fields validated but nothing is committed to the
dispatcher's queue.

```json
{
  "product_line": "TRS",
  "purpose": "Wireline crew rotation",
  "origin": "BASE-02",
  "destination": "ENF-62",
  "requested_departure": "2026-08-11T06:00:00+01:00",
  "time_window_minutes": 60,
  "expected_duration_minutes": 240,
  "passenger_count": 3,
  "cargo_weight_kg": 0,
  "revenue_classification": "REVENUE"
}
```

`400` when `product_line`, `origin`, `destination`, or
`revenue_classification` is absent. There is no free-text destination field to
fall back to — that is the point.

### `POST /bookings/parse/`

Natural-language booking. **Returns a draft payload for confirmation; does not
create anything.**

```json
{ "text": "3 people to ENF-62 Tuesday 06:00" }
```

```json
{
  "parsed": {
    "destination": "ENF-62",
    "passenger_count": 3,
    "requested_departure": "2026-08-11T06:00:00+01:00"
  },
  "unresolved": ["product_line", "origin", "revenue_classification"],
  "confidence": 0.91
}
```

The requester confirms and completes the unresolved fields. This removes the
friction that makes people bypass the system, without letting a model write a
cost-bearing record unattended.

### `POST /bookings/{ref}/submit/`

The transition that matters. On submit, the server:

1. Computes `lead_time_hours` and freezes it.
2. Sets `is_call_out` if inside the configured minimum lead time. **Server-side,
   not client-supplied.**
3. Runs the pooling match and returns any candidates.
4. Routes to `PENDING_APPROVAL` if call-out or above threshold, else `APPROVED`.

```json
{
  "booking_ref": "BK-202608-00417",
  "status": "PENDING_APPROVAL",
  "is_call_out": true,
  "lead_time_hours": 3.5,
  "call_out_reason_required": true,
  "pool_candidates": [
    {
      "trip_id": "TR-202608-00231",
      "origin": "BASE-02",
      "destination": "ENF-62",
      "planned_departure": "2026-08-11T06:00:00+01:00",
      "seats_free": 3,
      "cost_if_joined": 0.0,
      "cost_if_separate": 412.50
    }
  ]
}
```

`409` with `call_out_reason_required` when a call-out is submitted without a
reason code.

### Pooling

| Method | Path | Notes |
|---|---|---|
| `GET` | `/bookings/{ref}/pool-candidates/` | Matching trips on the same corridor within the time window |
| `POST` | `/bookings/{ref}/join/` | Body `{trip_id}`. Attaches the booking to an existing trip |
| `POST` | `/bookings/{ref}/decline-pool/` | Body `{reason}`. **`reason` is mandatory** — declining is the exception path |

Joining is the default in the UI. Declining requires a reason. Non-revenue trips
are 37.8% of all trips; that is the pool this is aimed at.

| Method | Path | Notes |
|---|---|---|
| `POST` | `/bookings/{ref}/approve/` | Approver role |
| `POST` | `/bookings/{ref}/reject/` | Body `{reason}` |
| `POST` | `/bookings/{ref}/cancel/` | Requester or dispatcher |
| `GET` | `/bookings/` | `?status=&product_line=&from=&to=&is_call_out=` |

---

## 3. Dispatch

### `GET /trips/{id}/assignment-options/`

Returns ranked vehicles with the cost of each choice, so the dispatcher sees the
difference between options rather than guessing.

```json
{
  "options": [
    {
      "vehicle": "12345-116-31",
      "class": "4X4_PICKUP",
      "ownership": "OWNED",
      "rank": 1,
      "estimated_cost": 318.00,
      "deadhead_km": 0,
      "utilisation_30d": 0.41,
      "reasons": ["owned before rental", "at origin base", "class matches load"]
    },
    {
      "vehicle": "98765-116-31",
      "ownership": "RENTAL",
      "rank": 2,
      "estimated_cost": 465.00,
      "deadhead_km": 22,
      "reasons": ["rental — owned unit available at lower cost"]
    }
  ]
}
```

Ranking rules, in priority order: **owned before rental**, right-size to load,
nearest available, rotate to equalise utilisation.

| Method | Path | Notes |
|---|---|---|
| `POST` | `/trips/` | Create from one or more approved bookings |
| `POST` | `/trips/{id}/assign/` | Body `{vehicle, driver, override_reason?}` — `override_reason` required when not choosing rank 1 |
| `POST` | `/trips/{id}/dispatch/` | Notifies driver; snapshots `seats_dispatched` |
| `GET` | `/trips/` | `?status=&vehicle=&driver=&from=&to=&is_pooled=` |
| `GET` | `/trips/{id}/` | Includes attached bookings, events, costs |

Overriding the optimiser is allowed and recorded. The override reason feeds the
owned-vs-rental KPI narrative — a ratio without reasons cannot be acted on.

---

## 4. Closure (mobile)

Offline-tolerant. The PWA queues these locally and replays them; `occurred_at`
is device time, `recorded_at` is server receipt.

| Method | Path | Notes |
|---|---|---|
| `POST` | `/trips/{id}/check-in/` | `{occurred_at, latitude, longitude}` |
| `POST` | `/trips/{id}/odometer/` | Multipart: `{reading_type, photo}` or `{reading_type, value_km, capture_method}` |
| `POST` | `/trips/{id}/events/` | Geofence and telematics events |
| `POST` | `/trips/{id}/close/` | The gate |
| `POST` | `/trips/{id}/standby/` | `{start\|end, location}` — records field standby as work |

### `POST /trips/{id}/odometer/`

Photo upload returns the OCR reading for confirmation:

```json
{
  "reading_type": "END",
  "ocr_value": 148302,
  "ocr_confidence": 0.97,
  "requires_confirmation": true
}
```

The driver confirms or corrects. `value_km` is set from the confirmation, never
from OCR alone.

### `POST /trips/{id}/close/`

```json
{ "error": "closure_incomplete", "missing": ["odometer_end"] }
```

`422` until odometer start, odometer end, and destination are all present. This
is the endpoint that makes data completeness reach 100% and stay there.

On success: computes `distance_km`, snapshots `destination_class`, assigns the
`accounting_period`, and enqueues costing.

---

## 5. Costing and reconciliation

Finance-role endpoints. No AI touches any of these paths.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/trips/{id}/costs/` | Cost lines with `allocation_basis` and `rule_version` |
| `POST` | `/trips/{id}/recost/` | Re-runs the engine. **`403` when the period is `CLOSED` or `LOCKED`** |
| `GET` | `/periods/` | |
| `POST` | `/periods/{year}-{month}/close/` | Freezes the period. Returns count of trips still open |
| `POST` | `/periods/{year}-{month}/reopen/` | Admin only, fully audited |
| `GET` | `/reports/reconciliation/?period=&product_line=` | Allocated vs invoiced vs GL, with variance bridge |
| `GET` | `/reports/accrual/?period=` | Trips taken but not yet invoiced |
| `POST` | `/invoices/` | Supplier invoice import |
| `GET` | `/reports/call-out-root-cause/?from=&to=` | Reason codes clustered by category and product line |
| `GET` | `/reports/contract-utilisation/?contract=` | Days paid vs days used |

`POST /periods/{p}/close/` refuses while trips remain open in the period, and
names them:

```json
{
  "error": "period_has_open_trips",
  "open_trip_count": 4,
  "trips": ["TR-202607-00892", "TR-202607-00901"]
}
```

---

## 6. KPIs and alerts

| Method | Path | Notes |
|---|---|---|
| `GET` | `/kpis/?from=&to=&product_line=` | Every KPI in `05-kpis-and-reporting.md` |
| `GET` | `/alerts/?severity=&resolved=false` | |
| `POST` | `/alerts/{id}/acknowledge/` | |
| `GET` | `/utilisation/?vehicle=&from=&to=` | Vehicle-day detail behind the headline number |

---

## 7. Conversational analytics

### `POST /ask/`

> *"What did TRS spend on transport last month?"*

Translates the question to a **parameterised query over the read-only BI views**,
executes it, and returns the number **with the query that produced it**.

```json
{
  "answer": "TRS transport cost for July 2026 was $84,210 across 212 trips.",
  "value": 84210.00,
  "query_used": "SELECT SUM(amount) FROM bi_cost_fact WHERE ...",
  "period_status": "CLOSED"
}
```

Constraints, non-negotiable:

- Read-only connection role. No DDL, no DML, statement timeout.
- Generated SQL is validated against an allowlist of views and columns.
- The model composes the *query*; the database computes the *number*. AI is
  never in the arithmetic path.
- Results carry `period_status`, so a figure from an open period is never
  mistaken for a closed one.

This puts answers in managers' hands without a BI request queue, while keeping
every number reproducible.

---

## 8. Permissions

| Role | Can |
|---|---|
| `requester` | Create, submit, cancel own bookings; view own history |
| `approver` | Approve/reject for their product line |
| `dispatcher` | Create trips, assign vehicles, override optimiser, close trips manually |
| `driver` | Check in/out, submit odometer, record standby for assigned trips only |
| `fleet_admin` | Masters, status changes, alert configuration, alias confirmation |
| `finance` | Costs, periods, invoices, reconciliation, recost within open periods |
| `bi_service` | `SELECT` on `bi_*` views only |

Object-level: drivers see only their assigned trips; requesters see only their
own bookings plus any trip they were pooled onto.

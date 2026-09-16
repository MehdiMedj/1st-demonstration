# Backlog

Sizing is relative: **S** ≈ 1–2 days, **M** ≈ 3–5 days, **L** ≈ 1–2 weeks,
**XL** ≈ needs breaking down before it is picked up.

`Blocks` / `Needs` express hard dependencies only. Anything not listed can run in
parallel.

---

## Phase 0 — Foundation

| ID | Title | Size | Needs | Notes |
|---|---|---|---|---|
| TRB-001 | Django project scaffold, settings split, Postgres, Docker Compose | M | — | `local` / `staging` / `production` settings; `btree_gist` enabled in the initial migration |
| TRB-002 | Auth, roles, and object-level permission framework | M | 001 | The seven roles in `02-api-surface.md` §8 |
| TRB-003 | Audit log — actor, action, before/after, on every model | M | 001 | Finance requires full traceability; retrofitting this is painful |
| TRB-004 | CI: pytest, ruff, mypy, migration-drift check, coverage gate | S | 001 | Migration drift check catches models edited without migrations |
| TRB-005 | Celery + Redis, beat schedule, dead-letter handling | S | 001 | |

**TRB-006 · Agree cost-centre mapping with Finance** — **XL, non-technical,
starts week one.** Twenty-one product lines in current fleet data mapped to the
chart of accounts, signed off by Finance and product line managers. This is a
Phase 3 deliverable that blocks Phase 1 master data. See OQ-1. *No code depends
on it shipping, but every code path depends on it being right.*

---

## Phase 1 — Capture

> **Outcome:** clean data at source; the daily Excel sheet is retired.

### Masters

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-010 | `ProductLine` model, admin, API | S | 002 | US-13 |
| TRB-011 | `Location` + `LocationAlias` models, admin, API | M | 001 | US-03 |
| TRB-012 | Seed location master — bases, rigs, airports, client sites, coordinates | M | 011 | US-03 |
| TRB-013 | Import 316 historical spellings as aliases; review queue | M | 012 | US-03 |
| TRB-014 | `VehicleClass` model and seed | S | 001 | US-11 |
| TRB-015 | `Vehicle` model with plate uniqueness and format `CHECK` | M | 014 | US-04 |
| TRB-016 | `VehicleStatusHistory` with `EXCLUDE USING gist` non-overlap | M | 015 | US-08 |
| TRB-017 | `Driver` model, admin, API | S | 002 | — |
| TRB-018 | `RentalContract` model, admin, API | S | 015 | US-19 |

### Migration

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-020 | **Dual-plate resolution** — split/merge 226 rows to 50 vehicles | L | 015 | US-04 |
| TRB-021 | Historical trip import with per-row rejection report | L | 020, 013 | — |
| TRB-022 | Migration reconciliation — row counts, cost totals, before/after | M | 021 | — |

> TRB-020 is the highest-risk ticket in Phase 1. It is data archaeology, not
> code: every one of the 226 rows needs a decision, and each decision needs to be
> recorded and reviewable. Budget for someone who knows the fleet to sit with it.

### Booking

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-030 | `BookingRequest` model, state machine, service layer | M | 010, 011 | US-01 |
| TRB-031 | Booking API — create, submit, cancel, list | M | 030 | US-01 |
| TRB-032 | Booking web form — typeahead, class suggestion, ≤60s target | L | 031 | US-01 |
| TRB-033 | Vehicle class suggestion from passengers and cargo | S | 014, 030 | US-01 |

### Dispatch and closure

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-040 | `Trip` model, state machine, `Trip 1—N BookingRequest` | M | 030, 015 | — |
| TRB-041 | Manual assignment — dispatcher queue and vehicle picker | M | 040, 017 | US-11 |
| TRB-042 | `TripEvent` append-only model and API | S | 040 | US-05 |
| TRB-043 | `OdometerReading` model, photo upload, storage | M | 040 | US-05 |
| TRB-044 | **Closure gate** — `CHECK` constraint + `422` with missing fields | M | 043 | US-06 |
| TRB-045 | Mobile PWA — check in/out, odometer capture, offline queue | XL | 042, 043 | US-05 |
| TRB-046 | Offline replay — conflict handling, device vs server time | M | 045 | US-05 |

### Utilisation

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-050 | `VehicleDay` model and nightly idempotent build | L | 040, 016 | US-07 |
| TRB-051 | Geofence arrival detection and destination classification | M | 012, 042 | US-07 |
| TRB-052 | `FIELD_STANDBY` derivation and manual declaration | M | 050, 051 | US-07 |
| TRB-053 | Utilisation API and rebuild command for any date range | S | 050 | US-08 |

### Phase 1 exit criteria

- [ ] Every vehicle has exactly one valid plate; 50 records, zero rejects
- [ ] Zero trips closable without odometer and destination — verified by
      attempting it in a test against the live schema
- [ ] Zero free-text destinations; every trip resolves to a master location
- [ ] Data completeness KPI ≥ 99% for four consecutive weeks
- [ ] The daily Excel sheet is switched off, not merely deprecated

> The last criterion is the real one. A retired sheet that is still being filled
> in means the app did not replace it.

---

## Phase 2 — Control

> **Outcome:** fewer trips for the same work.

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-060 | Corridor matching — same origin/destination within time window | L | 040, 012 | US-09 |
| TRB-061 | Pool candidate API with join-vs-separate cost comparison | M | 060, 090 | US-09 |
| TRB-062 | Join / decline endpoints; decline reason mandatory | M | 061 | US-09 |
| TRB-063 | Booking UI — joining as the default action | M | 062, 032 | US-09 |
| TRB-064 | Pooling rate and average occupancy KPIs | S | 062 | US-09 |
| TRB-070 | Lead-time config per product line; server-side call-out flag | M | 030 | US-10 |
| TRB-071 | `CallOutReasonCode` master, mandatory capture, narrative rule | S | 070 | US-10 |
| TRB-072 | Approval workflow, thresholds, notifications | M | 070, 002 | US-12 |
| TRB-073 | Call-out root-cause report by category and product line | M | 071 | US-10 |
| TRB-080 | Assignment optimiser — owned-first, right-size, nearest, rotate | L | 041, 050 | US-11 |
| TRB-081 | Cost-of-choice display per option | M | 080, 090 | US-11 |
| TRB-082 | Override reason capture and owned-vs-rental ratio reporting | S | 081 | US-11 |

### Phase 2 exit criteria

- [ ] Pooling rate reported weekly with a stated baseline and target
- [ ] 100% of call-outs carry a reason code
- [ ] Owned-vs-rental assignment ratio trending toward owned-first
- [ ] Declined pool offers all carry a reason

---

## Phase 3 — Visibility

> **Outcome:** transport cost lands on the owner's P&L.

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-090 | `CostAllocationRule` — versioned, date-effective, non-overlapping | M | 018 | US-13 |
| TRB-091 | Costing engine — rental share, fuel, call-out premium | L | 090, 044 | US-13 |
| TRB-092 | Pooled-trip allocation on the agreed basis | M | 091, 062 | US-13 |
| TRB-093 | `AccountingPeriod`, close/reopen, immutability trigger | M | 091 | US-14 |
| TRB-094 | Period close refuses while trips remain open; names them | S | 093 | US-14 |
| TRB-095 | Invoice import and invoice-line matching | M | 090 | US-15 |
| TRB-096 | Reconciliation report — allocated vs invoiced vs GL, variance bridge | L | 095, 093 | US-15 |
| TRB-097 | Accrual report — taken but not invoiced | M | 096 | US-15 |
| TRB-098 | Variance > 2% alert naming the responsible cost centres | S | 096 | US-15 |
| TRB-100 | Read-only `bi_*` views, versioned contracts | M | 091, 050 | US-16 |
| TRB-101 | Power BI semantic model — shared dimensions, facts | L | 100 | US-16 |
| TRB-102 | Retire the Excel consolidation step | S | 101 | US-16 |
| TRB-103 | Chargeback statement per product line per month | M | 092 | US-13 |

### Phase 3 exit criteria

- [ ] App-to-GL variance under 2% for two consecutive months
- [ ] Every cost line traces to trip, vehicle, and requester
- [ ] Excel consolidation removed from the month-end process
- [ ] Product line managers receive a chargeback statement they can query

---

## Phase 4 — Optimise

> **Outcome:** fleet sized to actual demand. **Not before Phase 1 data is
> trustworthy.**

| ID | Title | Size | Needs | Story |
|---|---|---|---|---|
| TRB-110 | Mobilisation plan import; 2–4 week rolling forward view | L | 030 | US-18 |
| TRB-111 | Demand prediction by product line — seasonal and rig-schedule | XL | 110, 021 | US-18 |
| TRB-112 | Capacity-vs-demand gap flagging | M | 111 | US-18 |
| TRB-113 | Quarterly fleet sizing report | M | 112, 050 | US-18 |
| TRB-120 | Contract-basis utilisation — days paid vs days used | M | 050, 018 | US-19 |
| TRB-121 | Renewal and low-utilisation alerts | S | 120 | US-19 |
| TRB-130 | Anomaly detection — fuel vs distance, odometer jumps | L | 091, 043 | US-20 |
| TRB-131 | Cost-per-km target monitoring by vehicle and class | M | 091 | US-20 |
| TRB-140 | Route and schedule optimisation | XL | 080, 111 | — |

---

## AI tickets (cross-phase)

Each of these is **suggestion-only**. None writes a value a human has not
confirmed, and none touches the costing path.

| ID | Title | Size | Phase | Story |
|---|---|---|---|---|
| TRB-150 | Destination normalisation — suggest aliases with confidence | M | 1 | US-03 |
| TRB-151 | Odometer photo OCR with confirmation step | M | 1 | US-05 |
| TRB-152 | Natural-language booking → draft payload | M | 1 | US-02 |
| TRB-153 | Pooling suggestions across product lines | M | 2 | US-09 |
| TRB-154 | Call-out justification clustering into themes | M | 2 | US-10 |
| TRB-155 | Conversational analytics over `bi_*` views, allowlisted SQL | L | 3 | US-17 |
| TRB-156 | Anomaly detection models | L | 4 | US-20 |

**TRB-157 · AI boundary test suite** — S, Phase 1, no dependencies. Asserts that
no AI-sourced value reaches `TripCost`, that `OdometerReading.value_km` is never
written from `ocr_value` without `confirmed_by`, and that the analytics SQL
allowlist rejects DDL and DML. Cheap to write, and it is what keeps the caution
in §5 of the brief true a year from now rather than merely intended.

---

## Suggested first sprint

TRB-001 → 005 (foundation), TRB-011, TRB-014, TRB-015 (the three masters that
everything else hangs off), and TRB-006 opened with Finance on day one.

TRB-020 — dual-plate resolution — should start its data review in parallel, since
it needs fleet knowledge rather than engineering time and will otherwise become
the critical path into Phase 2.

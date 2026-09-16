# Transport Booking Application — Engineering Overview

**Algeria Operations · Fleet & Transportation**

This directory converts the design brief into engineering artifacts: entity
definitions, an API surface, user stories, and a phased backlog.

| Document | Contents |
|---|---|
| `00-overview.md` | This file — scope, principle, architecture, glossary |
| `01-data-model.md` | Entities, fields, constraints, Django/Postgres notes |
| `02-api-surface.md` | REST endpoints, payloads, state transitions |
| `03-user-stories.md` | Stories by role, with acceptance criteria |
| `04-backlog.md` | Phased tickets with dependencies and sizing |
| `05-kpis-and-reporting.md` | KPI definitions, Power BI model, reconciliation |
| `06-decisions-and-risks.md` | Design decisions, deviations from the brief, open questions |

---

## 1. The governing principle

**The booking application is not a booking tool. It is the data capture layer
for the entire transport function.**

Every defect in the current dataset traces to one root cause: transport data is
entered by hand, after the fact, by someone who did not use the vehicle.

| Symptom | Evidence in current data | Structural fix |
|---|---|---|
| Mileage never recorded | 126 rows blank | Closure blocked without odometer |
| Vehicle identity unreliable | 226 rows carry two plates; only 50 real vehicles | One plate per record, format-validated, unique |
| Destination missing | 27 rows blank | Closure blocked without destination |
| Destination free-text | 316 spellings for a few dozen locations | Controlled location master + alias table |
| Call-out cost invisible | Three months read as zero | Call-out is a system-set flag with a cost line |

**Design rule:** no trip exists unless it was booked in the app, and no trip
closes without odometer and destination.

The rule is enforced in the database, not only in the UI. Constraints that live
in application code get bypassed by the next integration, the next data fix
script, or the next admin action.

---

## 2. Architecture

```
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Mobile (PWA)  │   │  Web (staff)   │   │  Telematics    │
│  driver check  │   │  request /     │   │  feed          │
│  in-out, odo   │   │  dispatch      │   │  (Phase 2+)    │
└───────┬────────┘   └───────┬────────┘   └───────┬────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                  ┌──────────────────────┐
                  │  Django + DRF API    │
                  │  ── booking          │
                  │  ── dispatch         │
                  │  ── closure          │
                  │  ── costing (det.)   │
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐        ┌──────────────┐
                  │  PostgreSQL          │───────▶│  Power BI    │
                  │  facts + dimensions  │ direct │  (DirectQuery│
                  └──────────┬───────────┘  conn  │   / Import)  │
                             │                     └──────────────┘
                             ▼
                  ┌──────────────────────┐
                  │  Celery workers      │
                  │  ── VehicleDay build │
                  │  ── alert rules      │
                  │  ── AI suggestions   │
                  └──────────────────────┘
```

**Stack decisions**

| Choice | Rationale |
|---|---|
| Django + DRF | Admin comes free — master-data maintenance (vehicles, locations, product lines, reason codes) is a first-class need, not an afterthought |
| PostgreSQL | Check constraints, exclusion constraints, and range types carry the integrity rules the brief demands; Power BI connects directly |
| Celery + Redis | Nightly `VehicleDay` build, alert evaluation, AI suggestion jobs |
| PWA for mobile | Drivers are on mixed devices in poor connectivity; offline-capable closure queue |
| No AI in the costing path | Costs must be deterministic, auditable, reproducible — see §5 of the brief |

The Excel consolidation step is removed entirely. Power BI reads the
application database.

---

## 3. Bounded contexts (Django apps)

| App | Owns |
|---|---|
| `masters` | Vehicle, VehicleClass, Location, LocationAlias, ProductLine, Driver, RentalContract |
| `booking` | BookingRequest, approval workflow, call-out classification |
| `dispatch` | Trip, assignment optimiser, pooling engine |
| `closure` | TripEvent, OdometerReading, geofence processing |
| `costing` | TripCost, CostAllocationRule, AccountingPeriod, Invoice, ReconciliationRun |
| `utilisation` | VehicleDay, KPI aggregates |
| `alerts` | Alert rules and dispatch |
| `intelligence` | AI adapters — NL booking, destination normalisation, pooling suggestions, anomaly flags. **Suggestion-only; writes nothing a human has not confirmed** |

---

## 4. Glossary

| Term | Meaning |
|---|---|
| **Booking request** | What a requester asks for. One per requester per journey. |
| **Trip** | One physical vehicle movement. May carry several booking requests — that is what pooling *is*. |
| **Pooled trip** | A trip with more than one booking request attached. |
| **Call-out** | A request submitted inside the minimum lead time. System-classified, never self-declared. |
| **Field standby** | A vehicle stationed at a rig site with zero km. **Working, not idle.** |
| **Vehicle-day** | One row per vehicle per calendar day, carrying its state. The unit of utilisation. |
| **Contract-basis utilisation** | Days paid for versus days used. The number that supports rate negotiation. |
| **Product line** | Cost centre. Must carry the same code as the finance chart of accounts. |
| **Period lock** | Once a month closes, its data freezes. Late entries post to the next open period. |
| **Revenue / non-revenue** | Declared at booking time, never inferred later. Non-revenue is currently 37.8% of trips. |

---

## 5. Phasing

| Phase | Scope | Outcome |
|---|---|---|
| **1 — Capture** | Masters, booking, assignment, mobile closure with odometer | Clean data at source; the daily Excel sheet is retired |
| **2 — Control** | Pooling engine, call-out lead-time rules, approval workflow | Fewer trips for the same work |
| **3 — Visibility** | Power BI model, cost-centre chargeback, monthly reconciliation | Transport cost lands on the owner's P&L |
| **4 — Optimise** | Demand prediction, route optimisation, contract right-sizing | Fleet sized to actual demand |

Phase 4 features must not precede trustworthy Phase 1 data. Optimisation on
unreliable data produces confident wrong answers.

**One dependency does not respect the phasing:** the cost-centre mapping with
Finance is a Phase 3 deliverable but a Phase 1 blocker. Twenty-one product lines
appear in current fleet data. Agreeing their mapping to the chart of accounts
must start in week one — see `06-decisions-and-risks.md`, OQ-1.

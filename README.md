# Transport Booking Application

**Algeria Operations · Fleet & Transportation**

Engineering specification and delivery backlog for the in-house transport
booking application, derived from the design brief in
[`docs/source/design-brief.md`](docs/source/design-brief.md).

No application code yet — this repository currently holds the specification the
build will follow.

---

## The principle

> **The booking application is not a booking tool. It is the data capture layer
> for the entire transport function.**

Every defect in the current transport dataset traces to one root cause: data is
entered by hand, after the fact, by someone who did not use the vehicle.

| Symptom | Current data | Structural fix |
|---|---|---|
| Mileage never recorded | 126 blank rows | Closure blocked without odometer |
| Vehicle identity unreliable | 226 dual-plate rows for 50 real vehicles | One plate per record, unique and validated |
| Destination missing | 27 blank rows | Closure blocked without destination |
| Destination free-text | 316 spellings | Controlled location master |
| Call-out cost invisible | 3 months read as zero | System-set flag with its own cost line |

**Design rule:** no trip exists unless it was booked in the app, and no trip
closes without odometer and destination — enforced in the database, not only in
the UI.

---

## Documents

| Document | Read it for |
|---|---|
| [`00-overview.md`](docs/00-overview.md) | Scope, architecture, bounded contexts, glossary |
| [`01-data-model.md`](docs/01-data-model.md) | Entities, fields, constraints, state machines |
| [`02-api-surface.md`](docs/02-api-surface.md) | REST endpoints, payloads, permissions |
| [`03-user-stories.md`](docs/03-user-stories.md) | 20 stories with acceptance criteria |
| [`04-backlog.md`](docs/04-backlog.md) | ~70 tickets, sized, sequenced, with dependencies |
| [`05-kpis-and-reporting.md`](docs/05-kpis-and-reporting.md) | KPI formulas, Power BI model, reconciliation |
| [`06-decisions-and-risks.md`](docs/06-decisions-and-risks.md) | Design decisions, deviations from the brief, risks, open questions |

**Start with `00-overview.md`.** If you are picking up work, go to
`04-backlog.md`. If you are Finance, `05-kpis-and-reporting.md` §3 and
`06-decisions-and-risks.md` §3 are the two that need your answers.

---

## Stack

Django + Django REST Framework, PostgreSQL, Celery/Redis, PWA for mobile
closure, Power BI reading the database directly.

Django admin is a deliberate part of the choice: master-data maintenance —
vehicles, locations, product lines, reason codes — is a first-class requirement,
not an afterthought.

---

## Phasing

| Phase | Scope | Outcome |
|---|---|---|
| **1 — Capture** | Masters, booking, assignment, mobile closure with odometer | Clean data at source; the daily Excel sheet is retired |
| **2 — Control** | Pooling engine, call-out rules, approval workflow | Fewer trips for the same work |
| **3 — Visibility** | Power BI model, chargeback, monthly reconciliation | Transport cost lands on the owner's P&L |
| **4 — Optimise** | Demand prediction, route optimisation, contract right-sizing | Fleet sized to actual demand |

Phase 4 must not precede trustworthy Phase 1 data. Optimisation on unreliable
data produces confident wrong answers.

---

## Two things that need answering before code starts

1. **The cost-centre mapping.** Twenty-one product lines appear in current fleet
   data. They must carry the same codes as the finance chart of accounts. This
   is nominally Phase 3 work, but it blocks Phase 1 master data and every
   reconciliation afterwards — see `04-backlog.md`, TRB-006.

2. **Nine open questions** in `06-decisions-and-risks.md` §3, each with a named
   owner and the ticket it blocks. Most are for Finance.

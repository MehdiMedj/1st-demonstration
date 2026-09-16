# User Stories

Format: **As a** role, **I want** capability, **so that** outcome — with
acceptance criteria that are testable, not aspirational.

Story IDs are referenced by the backlog tickets in `04-backlog.md`.

---

## Roles

| Role | Who they are |
|---|---|
| **Requester** | Anyone in a product line who needs a vehicle |
| **Approver** | Product line manager; owns the cost that lands on their P&L |
| **Dispatcher** | Assigns vehicles and drivers; today, takes the phone calls |
| **Driver** | Operates the vehicle; the only person who sees the odometer |
| **Fleet manager** | Owns utilisation, contracts, and the fleet size question |
| **Finance** | Reconciles transport cost to the GL |
| **Fleet admin** | Maintains master data |

---

## Phase 1 — Capture

### US-01 · Book a vehicle in under 60 seconds
**As a** requester, **I want** to book a vehicle faster than I could phone the
dispatcher, **so that** I have no reason to phone the dispatcher.

- [ ] Origin and destination are typeahead selections from the location master
- [ ] No free-text destination input exists anywhere in the form
- [ ] Product line defaults to the requester's assigned line, and is editable
- [ ] Revenue / non-revenue is a required two-way toggle with no default
- [ ] Vehicle class is suggested from passenger count and cargo weight
- [ ] A complete booking submits in ≤ 60 seconds on a mid-range phone
- [ ] Submitting an incomplete booking names every missing field at once

> This story is the adoption risk in `06-decisions-and-risks.md` (R-1). If it
> fails, nothing else in the system matters.

### US-02 · Book by typing a sentence
**As a** requester, **I want** to type *"3 people to ENF-62 Tuesday 06:00"*,
**so that** booking costs me no more effort than a WhatsApp message.

- [ ] Free text returns a pre-filled draft, never a committed booking
- [ ] Unresolved fields are listed explicitly and must be completed by hand
- [ ] Destination resolves through the alias table; an unmatched destination
      offers candidates and never invents a location
- [ ] The requester confirms before anything is created

### US-03 · Destination means one thing
**As a** fleet admin, **I want** every destination to resolve to one master
record, **so that** 316 spellings become a few dozen real locations.

- [ ] Location master seeded with bases, rig sites, airports, client facilities
- [ ] Each location tagged `BASE` or `FIELD`, with coordinates
- [ ] Historical spellings imported as aliases, mapped and reviewed
- [ ] AI-suggested aliases are inactive until an admin confirms them
- [ ] A confirmed alias resolves inbound text on the next request

### US-04 · One plate, one vehicle
**As a** fleet manager, **I want** each vehicle to exist exactly once, **so that**
utilisation is computed against 50 real vehicles rather than 226 ambiguous rows.

- [ ] `plate` is unique and format-validated at the database level
- [ ] Plates containing separators (`/ , ; & +`) are rejected on write
- [ ] The dual-plate rows are split or merged during migration, with a
      reconciliation report showing every decision
- [ ] Migration cannot complete while any plate fails validation

### US-05 · Close a trip with a photo, not a keyboard
**As a** driver, **I want** to photograph the odometer, **so that** I am not
typing numbers into a form at the end of a twelve-hour day.

- [ ] Check-in and check-out are two taps each
- [ ] Odometer capture is camera-first; OCR pre-fills the value
- [ ] The driver confirms or corrects the OCR value before it is stored
- [ ] Manual entry requires a reason and is flagged for review
- [ ] All actions queue offline and replay when connectivity returns
- [ ] Device time is preserved; server receipt time is recorded separately

### US-06 · A trip cannot close incomplete
**As a** fleet manager, **I want** closure blocked without odometer and
destination, **so that** blank-mileage and blank-destination rows stop existing.

- [ ] Closure returns `422` listing exactly what is missing
- [ ] The constraint holds at the database level, not only in the API
- [ ] Data completeness KPI reaches 100% and an alert fires on any regression
- [ ] Trips open past *N* hours after planned arrival raise an alert

### US-07 · Standby at a rig is work
**As a** fleet manager, **I want** a vehicle parked at a well with zero km
recorded as working, **so that** utilisation reflects reality rather than
punishing field deployment.

- [ ] `FIELD_STANDBY` is a first-class `VehicleDay` state
- [ ] Zero km on a `FIELD` location does not count as idle
- [ ] The nightly build derives standby from geofence position automatically
- [ ] A driver can also declare standby explicitly from mobile
- [ ] The dashboard's manual rig-site rule is retired

### US-08 · Decommissioned units leave quietly
**As a** fleet manager, **I want** disposed vehicles to exit utilisation
automatically, **so that** nobody maintains an exclusion list by hand.

- [ ] Status changes append to history with an effective date
- [ ] Overlapping status periods are rejected by the database
- [ ] All utilisation reporting reads status history, never current status
- [ ] Retiring the 6x6 and the 5T requires one status change each

---

## Phase 2 — Control

### US-09 · Offer the pool before the vehicle
**As a** requester, **I want** to be shown a departing vehicle I could join,
**so that** we stop sending two vehicles down the same road an hour apart.

- [ ] Matching runs at submit, before any new vehicle is assigned
- [ ] Candidates show origin, destination, departure, seats free, and the cost
      difference between joining and going separately
- [ ] Joining is the primary action; declining is secondary
- [ ] Declining requires a reason, stored and reportable
- [ ] Pooling rate is tracked as a first-class KPI from day one

### US-10 · Call-outs classify themselves
**As an** approver, **I want** late requests flagged automatically, **so that**
call-out cost stops being invisible.

- [ ] `is_call_out` is set server-side from lead time; users cannot set it
- [ ] Minimum lead time is configurable per product line
- [ ] A reason code is mandatory; `OTHER` forces a narrative
- [ ] Call-outs escalate for approval and carry a premium cost line
- [ ] The premium is charged wholly to the requesting product line
- [ ] Reason codes accumulate into a root-cause report

> Call-outs are 35 trips and $10,269 — the single largest exception on the
> scorecard. The reason codes are the deliverable; the flag alone changes nothing.

### US-11 · See what the choice costs
**As a** dispatcher, **I want** each assignment option priced, **so that** I can
see what choosing the rental instead of the owned unit costs.

- [ ] Options ranked: owned before rental, right-sized, nearest, then rotation
- [ ] Every option shows estimated cost and deadhead km
- [ ] Choosing anything other than rank 1 requires a recorded reason
- [ ] Owned-vs-rental assignment ratio is reportable, with override reasons

### US-12 · Approve what deserves approval
**As an** approver, **I want** only exceptions in my queue, **so that** I read
them instead of rubber-stamping everything.

- [ ] Routine in-lead-time requests auto-approve
- [ ] Call-outs and above-threshold requests route to approval
- [ ] Thresholds are configurable per product line
- [ ] Approval and rejection are notified to the requester with the reason

---

## Phase 3 — Visibility

### US-13 · Cost lands on the owner's P&L
**As** Finance, **I want** every trip cost allocated to a product line, **so
that** transport appears on the P&L of whoever caused it.

- [ ] Every cost line carries a product line and an `allocation_basis` string
- [ ] Product line codes match the finance chart of accounts exactly
- [ ] Pooled-trip costs split on the agreed basis, shown per booking
- [ ] Call-out premium is not shared across the pool

### US-14 · The month closes like the GL closes
**As** Finance, **I want** period lock, **so that** a closed month cannot move.

- [ ] Closing a period is refused while trips remain open, and names them
- [ ] Closed-period cost lines reject update and delete at the database level
- [ ] Late entries post to the next open period
- [ ] Reopening is admin-only and fully audited

### US-15 · Reconcile to the GL inside 2%
**As** Finance, **I want** an allocated-vs-invoiced-vs-GL report, **so that** I
can sign off transport cost each month.

- [ ] Report runs per period, per cost centre
- [ ] Variance shown in amount and percent, with a documented bridge
- [ ] Accrual figure produced for trips taken but not yet invoiced
- [ ] Every cost line traces to a trip, a vehicle, and a requester
- [ ] Variance above 2% raises an alert naming the cost centres responsible

### US-16 · Power BI reads the database
**As a** fleet manager, **I want** the dashboard connected directly, **so that**
the Excel consolidation step disappears.

- [ ] Read-only BI views for trip, cost, vehicle, location, product line, date
- [ ] Semantic model uses shared dimensions across all facts
- [ ] Zero manual re-keying between the application and the dashboard
- [ ] View contracts are versioned; base-table refactors do not break reports

### US-17 · Ask a question, get a number
**As a** product line manager, **I want** to ask *"what did TRS spend on
transport last month?"*, **so that** I am not queued behind a BI request.

- [ ] Answers are computed by the database, never by the model
- [ ] Generated SQL is validated against a view and column allowlist
- [ ] The query used is returned alongside the answer
- [ ] Open-period figures are labelled as provisional
- [ ] The connection role is read-only with a statement timeout

---

## Phase 4 — Optimise

### US-18 · Forecast the next four weeks
**As a** fleet manager, **I want** a rolling forward view by product line, **so
that** call-outs become scheduled trips.

- [ ] Two-to-four-week forward view from the mobilisation plan
- [ ] Predicted demand compared against available capacity
- [ ] Gaps flagged early enough to plan rather than call out

### US-19 · Right-size the contracts
**As a** fleet manager, **I want** contract-basis utilisation, **so that** I can
negotiate on evidence.

- [ ] Days paid versus days used, per contract and per unit
- [ ] Alert before auto-renewal, at `end_date - notice_period_days`
- [ ] Alert when a unit falls below the utilisation threshold
- [ ] Quarterly fleet sizing report from actual demand

### US-20 · Catch the numbers that do not add up
**As a** fleet manager, **I want** anomalies flagged, **so that** fuel and
distance stop disagreeing silently.

- [ ] Fuel drawn versus distance recorded, flagged beyond tolerance
- [ ] Implausible odometer jumps flagged against class daily maxima
- [ ] Cost per km above target, per vehicle and per class
- [ ] Flags are advisory and never alter a cost line automatically

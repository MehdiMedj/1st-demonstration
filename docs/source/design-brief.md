# Transport Booking Application — Design Brief

**Algeria Operations · Fleet & Transportation**
Prepared as input to the in-house AI-assisted booking application, and to the Power BI / finance reconciliation workstream.

---

## 1. The single principle that should shape the build

**The booking application is not a booking tool. It is the data capture layer for the entire transport function.**

Every problem the dashboard exposed traces back to one root cause: transport data is entered by hand, after the fact, by someone who is not the person who used the vehicle. The consequences are measurable in the current dataset:

| Symptom | Evidence in current data |
|---|---|
| Mileage never recorded | 126 rows with blank mileage |
| Vehicle identity unreliable | 226 rows carry two plates in one field; only 50 real vehicles exist |
| Destination missing | 27 rows with no destination |
| Destination free-text | 316 distinct spellings for a few dozen real locations |
| Call-out cost invisible | Three months of spend read as zero until corrected |

If the app only automates booking and leaves the daily sheet in place, none of this is fixed. If the app *becomes* the record — booking → trip → closure → cost — then the dashboard, Power BI and the P&L reconciliation all inherit clean data with no re-keying.

**Design rule: no trip exists unless it was booked in the app, and no trip closes without odometer and destination.**

---

## 2. Module map

### 2.1 Trip request (the front door)

Captures at request time, not afterwards:

- Requester, **product line (= cost centre)**, purpose
- Origin, destination — **selected from a controlled location master, never free text**
- Date, time window, expected duration
- Passengers / cargo, so the right vehicle class is assigned
- **Revenue-generating vs non-revenue** — declared at booking, not inferred later

The product line field is the single most valuable thing on this screen. It is what makes chargeback and P&L reconciliation possible.

### 2.2 Pooling engine — now that pooling is live

This is where the app earns its cost. Before any new vehicle is assigned:

- Match the request against approved trips on the same corridor within a time window
- Show the requester: *"A vehicle departs Base 02 → ENF-62 Berkine at 06:00 with 3 seats free — join?"*
- Make joining the **default**, and require a reason to decline it
- Track **pooling rate** (% of trips that shared a vehicle) as a first-class KPI

Non-revenue trips are currently **37.8%** of all trips. That is the pool the pooling engine is aimed at.

### 2.3 Vehicle assignment optimiser

Assignment rules, in priority order:

1. **Owned before rental.** Owned vehicles run at ~46% utilisation while rentals are hired alongside them. Every owned-vehicle trip displaces a rental day.
2. **Right-size to load.** Do not dispatch a 4x4 to carry one passenger to Algiers.
3. **Nearest available**, to cut deadhead running.
4. **Rotate** to equalise utilisation and even out wear.

Each assignment should display the cost of the choice, so the dispatcher sees the difference between options.

### 2.4 Trip closure and auto-capture

- Driver checks in / out on mobile; **odometer photo or telematics feed**, not typed
- GPS geofence auto-detects arrival and classifies destination as **base or rig site**
- **Rig-site standby is a status, not a gap.** A vehicle stationed at a well with zero kilometres must be recorded as working — the dashboard currently applies this as a manual rule; the app should record it natively
- Trip cannot close without odometer and destination — this eliminates the blank-mileage and blank-destination rows

### 2.5 Call-out control

Call-outs are **35 trips, $10,269** — the single largest exception on the scorecard.

- Any request inside the minimum lead time is automatically classified as a call-out
- Requires **justification and a reason code** (rig delay, equipment failure, client request, planning miss…)
- Escalates for approval, and is charged to the requesting product line at the premium rate
- Reason codes accumulate into a root-cause report — that is what actually reduces call-outs

### 2.6 Demand planning link

Connect the booking pipeline to the **mobilisation plan and revenue forecast** already modelled:

- Two-to-four-week rolling forward view of expected trips by product line
- Converts call-outs from surprises into scheduled trips
- Feeds quarterly fleet sizing: how many units do we actually need next quarter?

### 2.7 Contract and cost engine

- Register of rental contracts (currently **35 units, $40,553/month**) with rates and end dates
- Every trip carries its cost: rental share + fuel + call-out premium
- **Contract-basis utilisation**: days paid for versus days used — the number for rate negotiations
- Alerts before auto-renewal, and when a unit falls below the utilisation threshold

### 2.8 Exception and alert engine

Push, don't wait to be asked:

- Vehicle idle at base more than *N* consecutive days
- Utilisation below threshold over a rolling 30 days
- Cost per km above target for a vehicle or class
- Fuel drawn inconsistent with distance recorded
- Rental contract approaching renewal

---

## 3. Data model — the part that determines whether Power BI and finance ever reconcile

Get this right and everything downstream is easy. Get it wrong and you rebuild in a year.

**Vehicle master**
- One row per physical vehicle. **One plate per record, format-validated** — this alone prevents the 226 dual-plate rows
- Type, class, ownership (owned/rental), contract reference, daily rate, fuel rate, status (active / standby / workshop / off-hire / disposed)
- Status history, so decommissioned units (like the 6x6 and the 5T) leave utilisation automatically instead of by manual exclusion

**Location master**
- Controlled list: bases, rig sites, airports, client facilities
- Each tagged **base vs field** — this is what makes the rig-site rule automatic rather than a keyword list
- Coordinates for geofencing and distance estimation

**Trip fact table**
- `trip_id`, `booking_ref`, date, vehicle, driver, **product line / cost centre**, trip type, origin, destination, destination class, planned vs actual km, hours, status, pooled-with reference, call-out flag and reason code, cost components

**Cost centre alignment**
- Product lines in the app **must use the same codes as the finance chart of accounts**. Twenty-one product lines currently appear in the fleet data — agree the mapping with Finance before build, not after.

---

## 4. Power BI and P&L reconciliation

**Architecture:** application database → Power BI direct connection. The Excel consolidation step disappears entirely.

**Semantic model:** shared dimensions for Date, Vehicle, Location, Product Line/Cost Centre, Contract. Facts for Trips, Costs, Call-outs.

**Reconciliation design — this is what Finance will ask for:**

1. **Period lock.** Once a month is closed, freeze the data. Late entries post to the next period, exactly as the GL works.
2. **Allocated vs invoiced.** Trip-level allocated cost on one side, rental invoices and fuel invoices on the other, with the variance explained.
3. **Reconciliation report:** total transport cost in the app versus the GL account balance, per cost centre, per month, with a documented variance bridge.
4. **Accrual support.** At month end the app should produce the accrual figure for trips taken but not yet invoiced.
5. **Audit trail.** Every cost line traceable to a trip, a vehicle and a requester.

Aim for a variance under 2% between the app and the GL. Anything wider means the cost-centre mapping is wrong, and it is better to find that in month one.

---

## 5. Where AI genuinely helps

Since the build is already AI-assisted, these are the uses that pay:

| Use | Why it matters |
|---|---|
| **Natural-language booking** — *"3 people to ENF-62 Tuesday 06:00"* → structured request | Removes the friction that makes people bypass the system |
| **Destination normalisation** | 316 spellings collapse to a clean master automatically |
| **Pooling suggestions** | Finds merge opportunities a dispatcher would miss across product lines |
| **Demand prediction** | Learns seasonal and rig-schedule patterns; drives fleet sizing |
| **Anomaly detection** | Flags fuel-versus-distance mismatches, implausible odometer jumps |
| **Conversational analytics** — *"what did TRS spend on transport last month?"* | Puts answers in managers' hands without a BI request queue |
| **Call-out root-cause clustering** | Groups free-text justifications into recurring themes |

**One caution:** keep AI out of the cost calculation itself. Costs must be deterministic, auditable and reproducible for Finance. Use AI for classification, suggestion and prediction — never for the number that lands in the P&L.

---

## 6. Suggested phasing

| Phase | Scope | Outcome |
|---|---|---|
| **1 — Capture** | Booking + assignment + mobile closure with odometer; vehicle and location masters | Clean data at source; the daily Excel sheet is retired |
| **2 — Control** | Pooling engine, call-out lead-time rules, approval workflow | Fewer trips for the same work |
| **3 — Visibility** | Power BI model, cost-centre chargeback, monthly reconciliation with Finance | Transport cost lands on the owner's P&L |
| **4 — Optimise** | Demand prediction, route and schedule optimisation, contract right-sizing | Fleet sized to actual demand |

Resist building Phase 4 features before Phase 1 data is trustworthy. Optimisation on unreliable data produces confident wrong answers.

---

## 7. KPIs the application should own

Beyond the current scorecard:

- **Pooling rate** — share of trips that shared a vehicle *(new, now that pooling is live)*
- **Average occupancy** — seats used versus seats dispatched
- **Booking lead time** — the leading indicator for call-outs
- **Owned-vs-rental assignment ratio** — is the owned fleet being used first?
- **Right-sizing rate** — trips where vehicle class matched the load
- **Data completeness** — % of trips closed with odometer and destination *(this should reach 100% and stay there)*
- **Contract-basis utilisation** — days paid for versus days used

---

## 8. Two risks worth naming early

**Adoption.** If booking through the app is slower than phoning the dispatcher, people will phone the dispatcher. The system only works if it is the *only* way to get a vehicle — that requires management backing, not a better interface.

**Chargeback politics.** Charging transport to product-line P&Ls is the strongest cost lever available, and it will be resisted the moment it becomes real money. Agree the allocation method with Finance and the product line managers *before* go-live, not after the first invoice.

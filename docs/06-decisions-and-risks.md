# Design Decisions, Deviations, Risks, and Open Questions

---

## 1. Design decisions

### DD-1 · Booking and Trip are separate entities

**Brief:** the trip fact table carries a *"pooled-with reference"*.

**Decision:** model `Trip 1 ── N BookingRequest` instead. A trip is one physical
vehicle movement; a booking is one person's request. Pooling is simply a trip
with more than one booking attached.

**Why:** a pooled-with self-reference works for two trips and breaks at three.
Four bookings sharing a vehicle would produce four trip rows cross-referencing
each other, and every KPI would then have to decide whether to count one trip or
four — which is exactly how a metric acquires two definitions. With the parent
model, distance is recorded once, cost is allocated once and split, and pooling
rate is `count(bookings) > 1`.

**Cost:** cost allocation across attached bookings becomes a real calculation
rather than a copy. That calculation is unavoidable regardless of the model —
this way it happens in one place.

### DD-2 · `VehicleDay` is the utilisation grain

**Brief:** *"rig-site standby is a status, not a gap"* — currently applied as a
manual dashboard rule.

**Decision:** a nightly-built row per vehicle per day carrying its state.

**Why:** utilisation asked of trips is a question about gaps, and gaps are
ambiguous — a vehicle at a well with zero km looks identical to a vehicle
forgotten in a car park. Making the day the grain turns the rig-site rule from
a keyword heuristic into a stored fact, and makes the app and Power BI count
rows in the same table rather than reimplementing the same rule twice.

**Cost:** a nightly job that must be idempotent and rebuildable. Worth it.

### DD-3 · Integrity lives in the database

**Decision:** the closure gate, plate uniqueness, status non-overlap, and period
immutability are Postgres constraints and triggers, not only serializer
validation.

**Why:** every rule in the brief exists because a previous rule was bypassed.
Django validators do not run on `bulk_update`, `QuerySet.update()`, migrations,
admin actions in some paths, or a psql session at 22:00 during a month-end fix.
The 126 blank-mileage rows are what "validated in the application layer" looks
like after two years.

**Cost:** constraint changes require migrations and brief locks. Acceptable.

### DD-4 · AI suggests; humans and the database decide

**Brief:** *"keep AI out of the cost calculation itself."*

**Decision:** extended slightly — AI output lands in a *separate field* from the
authoritative one everywhere, not just in costing. `ocr_value` beside `value_km`.
`LocationAlias.confidence` with `confirmed_at` gating activation. Parsed booking
payloads returned for confirmation rather than created.

**Why:** the brief's caution is right but stated at the costing boundary only.
Distance feeds cost. A wrong OCR odometer is a wrong cost even though no AI ran
in the costing engine. Separating suggested from authoritative at every capture
point makes the boundary structural instead of a matter of discipline.

**Enforcement:** TRB-157, a test suite asserting the boundary holds.

### DD-5 · Approval is for exceptions only

**Decision:** in-lead-time, below-threshold requests auto-approve. Only
call-outs and above-threshold requests route to an approver.

**Why:** R-1 below. Every approval step is a reason to phone the dispatcher
instead. Friction should be spent where it changes behaviour — on the late
request that costs a premium — and nowhere else.

### DD-6 · `destination_class` is snapshot at closure

**Decision:** copy `BASE`/`FIELD` onto the trip at closure rather than joining
to the location master at read time.

**Why:** if a location is reclassified in 2027, every historical utilisation
figure would silently restate, and a closed, reconciled period would stop
matching the GL. Facts record what was true when they happened.

---

## 2. Risks

### R-1 · Adoption — the system must be the only way to get a vehicle

*From the brief:* if booking through the app is slower than phoning the
dispatcher, people will phone the dispatcher.

This is the risk that decides the project. Everything else is recoverable.

**Mitigations in this spec:**
- US-01 sets a hard 60-second booking target, treated as a test, not an aim
- US-02 natural-language booking makes the fast path faster than a phone call
- DD-5 keeps approval out of the routine path
- Mobile closure is two taps and a photo — no typing at the end of a long day

**Mitigation that is not in this spec, and matters more than the ones that are:**
management backing, and a dispatcher who is instructed to refuse unbooked
requests. That is an operational decision, not a feature. The brief says this
plainly and it should not be softened.

**Leading indicator to watch:** trips created by dispatchers on behalf of
requesters. If that rises, people are still phoning; the app is just recording
the call afterwards, which reproduces the original problem with a new interface.

### R-2 · Chargeback politics

*From the brief:* charging transport to product-line P&Ls is the strongest cost
lever available, and it will be resisted the moment it becomes real money.

**Mitigation:** run Phase 3 in **shadow mode for one full period** — produce
chargeback statements and reconciliation, distribute them, change no ledger.
Disputes surface against a statement nobody has paid, which is a far cheaper
argument. Agree the allocation method with Finance and product line managers
before go-live, not after the first invoice.

The most likely dispute is pooled-trip allocation (OQ-2). A manager whose
booking joined someone else's trip will ask why they carry any cost at all.
Decide, document, and communicate that before the first statement, not in
response to the first complaint.

### R-3 · The location master rots

316 spellings became 316 spellings because free text was available and nobody
owned the list. Removing the free-text field is necessary but insufficient — a
controlled list with no maintainer produces `OTHER — see notes` within six
months.

**Mitigation:** a named owner, a request path for new locations with a target
turnaround measured in hours, and a monthly report of alias-resolution failures.
If requesters cannot get a location added quickly, they will find a way around
the controlled list, and the way around it will be worse than free text.

### R-4 · Offline closure versus period lock

Drivers work where there is no signal. A trip closed on the 31st may reach the
server on the 2nd, after the period closed.

**Mitigation:** `occurred_at` (device) is stored separately from `recorded_at`
(server). Period assignment follows `occurred_at` while the period is open. Once
closed, the cost posts to the next open period with the original trip date
retained on the trip — matching how the GL handles late entries. See OQ-3 for
the tolerance window Finance must set.

### R-5 · Migration is the critical path, and it is not an engineering task

TRB-020 requires deciding what each of 226 dual-plate rows actually meant. That
needs someone who knows the fleet, not someone who knows Django. If it starts
when engineering reaches it, it becomes the critical path into Phase 2.

**Mitigation:** start the data review in parallel with Phase 0.

### R-6 · Driver location tracking is personal data

Geofencing and telematics track named individuals continuously, which carries
legal and industrial-relations weight independent of the technology.

**Mitigation:** confirm the lawful basis and any works-council or contractual
requirements before TRB-045 ships. Retain fine-grained position data on a stated
schedule and derive `VehicleDay` from it, rather than keeping raw traces
indefinitely. Restrict position history to fleet and safety roles — a product
line manager needs the cost, not the route.

This is flagged because it is easier to design for now than to retrofit after
go-live. It is a question for Legal and HR, not for engineering.

---

## 3. Open questions

Each needs an owner and an answer before the ticket that depends on it starts.

| ID | Question | Blocks | Owner |
|---|---|---|---|
| **OQ-1** | The mapping of 21 product lines to the finance chart of accounts. Are all 21 real cost centres, or are some duplicates and typos of the same one? | TRB-010, all of Phase 3 | Finance + Fleet |
| **OQ-2** | Pooled-trip allocation basis. Proposed: passenger-km share, with call-out premium charged wholly to the late requester. Needs Finance and product line sign-off. | TRB-092 | Finance + PL managers |
| **OQ-3** | Late-closure tolerance. How many days after period close may a trip still post to its original period before it moves to the next? | TRB-093 | Finance |
| **OQ-4** | Minimum lead time defining a call-out. Uniform, or per product line? A wireline callout and an office transfer plausibly differ. | TRB-070 | Fleet + Operations |
| **OQ-5** | Owned-vehicle daily rate basis — depreciation, internal transfer rate, or fully-loaded cost? Determines whether owned-first is genuinely cheaper or only appears so. | TRB-090 | Finance |
| **OQ-6** | Fuel cost source: issued-fuel records, invoices, or consumption rate × distance? The brief implies a rate; reconciliation needs actuals. | TRB-091 | Finance + Fleet |
| **OQ-7** | Is a dispatcher permitted to create a trip with no prior booking — for a genuine emergency? If yes it needs a reason code and a data-quality KPI. If no, that must be operationally enforceable, or people will phone anyway. | TRB-040 | Fleet management |
| **OQ-8** | Retention period for GPS traces and odometer photos. | TRB-045 | Legal + HR |
| **OQ-9** | Do rig-standby days consume rental days at full rate? Determines whether contract-basis utilisation counts standby as used. | TRB-120 | Procurement |

**OQ-7 deserves particular attention.** The brief's design rule — *no trip
exists unless it was booked in the app* — is correct as an intent, but reality
will produce a movement that was genuinely never booked: a medical evacuation,
a breakdown recovery. If the system has no legitimate path for it, the trip
happens anyway and goes unrecorded, which is the exact failure the whole
application exists to prevent. A retro-booking path with a mandatory reason
code, counted and reported as a data-quality metric, keeps the record complete
while keeping the pressure visible. The alternative — no path at all — does not
eliminate unbooked trips; it only eliminates the evidence of them.

# Navis-Lite: Intelligent Yard & Gate Control System

A containerized MVP replica of a Terminal Operating System (TOS), modeled after Navis N4.
Simulates an automated freight terminal: truck gate check-in, ISO 6346 validation,
ML-driven yard slot placement (the "Expert Decking" engine), reefer power-zone routing,
live telemetry simulation, and a digital-twin yard dashboard.

## Architecture

| Layer | Tech | Responsibility |
|---|---|---|
| `gateway-service/` | Java 17, Spring Boot, Spring Data JPA, MySQL Connector/J | Gate check-in REST API, ISO 6346 validation, transaction persistence |
| `decking-engine/` | Python, FastAPI, Pandas, NumPy, Scikit-learn | Slot placement algorithm, stacking rules, relocation advice, reefer Block-R routing, telemetry simulation |
| `dashboard/` | React | Operational Ledger, Digital Twin Yard Matrix, Alert Ticker |
| `mysql` | MySQL 8 | Terminal state (gate transactions, yard slots) |

Data flow: truck arrives → `gateway-service` validates ISO 6346 format + weight →
persists transaction → synchronously calls `decking-engine` at `/api/predict-decking` →
decking engine applies the stacking constraint (a container may only rest on one at
least as heavy), the reefer Block-R power-zone filter, and an ML dwell-time/shuffle-risk
score → returns a slot assignment, or a rejection carrying the single best relocation
that would make room → `gateway-service` persists final placement → `dashboard` polls
both services and renders the ledger, yard grid, relocation advice, and any live
telemetry alerts.

## Running locally

```bash
cp .env.example .env
docker compose up --build
```

- Dashboard: http://localhost:3000
- Gateway API: http://localhost:8080/api/gate/check-in
- Decking Engine API: http://localhost:8000/api/predict-decking (docs at `/docs`)
- MySQL: localhost:3306

## Repository layout

```
navis-lite/
├── docker-compose.yml
├── .env.example
├── gateway-service/     # Java Spring Boot gate API
├── decking-engine/      # Python FastAPI decking algorithm + telemetry
└── dashboard/            # React digital twin UI
```

## Business rules

- **ISO 6346**: container IDs must match `[A-Z]{4}\d{7}` (4 uppercase letters + 7 digits).
- **Stacking policy**: tier 1 is the ground and accepts anything, so a container
  arriving at an empty yard is always placed rather than turned away. Above ground a
  container may only rest on one at least as heavy, so stacks build heaviest-at-the-
  bottom — a heavier box on a lighter one risks crushing its corner posts and raises
  the stack's centre of gravity. Stacks also fill bottom-up; no floating slots.
- **Relocation advice**: when nothing is legal, the engine does not simply reject. It
  searches for the single best housekeeping move that would make the container
  placeable — a container with nothing stacked on it, that has somewhere legal to go,
  and whose slot once freed genuinely accepts the arrival. Candidates are ranked by
  the destination's own shuffle risk (so the move does not create tomorrow's rehandle)
  plus a penalty for disturbing cargo that is about to depart. The system proposes;
  a crane operator decides. Nothing is moved automatically.
- **Reefer routing**: containers flagged `REEFER` may only be placed in powered
  slots within `Block-R`.
- **Telemetry alerts**: the decking engine runs a background simulation loop over
  active reefer slots; a power loss or temperature threshold breach raises a
  high-priority alert consumed by the dashboard's Alert Ticker.

## The dwell-time model

Slot ranking depends on predicting how long a container will occupy a slot. That
prediction is learned, selected and measured rather than assumed.

**Training data comes from real operating history.** The engine pulls raw gate
transactions from `GET /api/gate/training-data` and does its own wrangling in
`decking-engine/app/services/training_data.py`:

- containers that never received a slot (rejected or held at the gate) are dropped —
  there is no placement to learn from;
- **right-censored** observations — containers still sitting in the yard, whose true
  dwell is unknown and only bounded below — are excluded from the target, because
  treating a lower bound as a completed value biases every prediction downward.
  Excluding them is not free either (it skews the sample toward fast-moving cargo),
  so the censoring rate is measured and reported in the model metrics instead of
  being hidden;
- non-positive dwell from clock skew and implausibly long dwell are dropped as data
  faults;
- `is_heavy` is engineered from the 20,000 kg structural threshold.

Below `MIN_TRAINING_ROWS` usable rows the model falls back to a synthetic corpus, so
a terminal on day one still works. `POST /api/model/retrain` promotes the model onto
real history once enough moves have accumulated, without a restart.

**The model is selected by measurement, not preference.** Every training run
cross-validates a `LinearRegression` and a `RandomForestRegressor` and deploys
whichever has the lower MAE, then measures the winner on a held-out test set and
against a naive mean-predicting baseline.

That measurement produced a finding worth recording: **on the synthetic corpus the
RandomForest does not earn its complexity.** Linear regression scores a lower MAE
(0.810 vs 0.830 days) at a fraction of the cost, because the synthetic generator
builds dwell from a linear formula. The engineered `is_heavy` feature also scored
0.0 importance under the tree — it is collinear with a threshold the tree can split
on directly. Both models beat the naive baseline by roughly 28%, so the prediction
is worth making; it simply does not need an ensemble to make it. If real terminal
history turns out to be non-linear, the same selection step will promote the forest
on merit.

`GET /api/model/metrics` exposes the whole picture live — selected model, the
candidate comparison, MAE / RMSE / R², cross-validated MAE and spread, baseline
comparison, feature attribution, and the data provenance including how many rows
were dropped and why.

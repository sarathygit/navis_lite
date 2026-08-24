# Navis-Lite: Intelligent Yard & Gate Control System

A containerized MVP replica of a Terminal Operating System (TOS), modeled after Navis N4.
Simulates an automated freight terminal: truck gate check-in, ISO 6346 validation,
ML-driven yard slot placement (the "Expert Decking" engine), reefer power-zone routing,
live telemetry simulation, and a digital-twin yard dashboard.

## Architecture

| Layer | Tech | Responsibility |
|---|---|---|
| `gateway-service/` | Java 17, Spring Boot, Spring Data JPA, MySQL Connector/J | Gate check-in REST API, ISO 6346 validation, transaction persistence |
| `decking-engine/` | Python, FastAPI, Pandas, NumPy, Scikit-learn | Slot placement algorithm, weight-tier rules, reefer Block-R routing, telemetry simulation |
| `dashboard/` | React | Operational Ledger, Digital Twin Yard Matrix, Alert Ticker |
| `mysql` | MySQL 8 | Terminal state (gate transactions, yard slots) |

Data flow: truck arrives → `gateway-service` validates ISO 6346 format + weight →
persists transaction → synchronously calls `decking-engine` at `/api/predict-decking` →
decking engine applies weight-tier constraint (>20,000 kg → Tier 1-2 only), reefer
Block-R power-zone filter, and an ML dwell-time/shuffle-risk score → returns slot
assignment → `gateway-service` persists final placement → `dashboard` polls both
services and renders the ledger, yard grid, and any live telemetry alerts.

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
- **Weight-tier policy**: containers over 20,000 kg are restricted to Tier 1 or 2;
  lighter containers are routed to Tier 3, 4, or 5.
- **Reefer routing**: containers flagged `REEFER` may only be placed in powered
  slots within `Block-R`.
- **Telemetry alerts**: the decking engine runs a background simulation loop over
  active reefer slots; a power loss or temperature threshold breach raises a
  high-priority alert consumed by the dashboard's Alert Ticker.

# Team Charter — Real-Time Crypto Volatility Detection

## Team Members & Roles

| Member | Primary Role | Core Responsibilities |
| :--- | :--- | :--- |
| *Rico Pichardo Abreu* | Model Lead & Ops | Model architecture, CI/CD, Monitoring (Prometheus/Grafana), SLOs, & Drift (M5-M7). |
| *Honey Streak* | Infrastructure Lead & Ops | FastAPI deployment, Docker Compose, Kafka/MLflow, CI/CD, & System Stability (M5-M7). |
| *Swetaleena Guha* | Pipeline, Testing & Docs | Replay pipeline execution, integration testing, system documentation, and QA. |
| *Irene John* | Pipeline, Testing & Docs | Replay pipeline execution, integration testing, system documentation, and QA. |

---

## Project Objectives
The objective was to engineer a production-ready, real-time AI service for detecting cryptocurrency volatility. The system ingests live BTC-USD tick data, processes features in real-time, serves predictions via a FastAPI endpoint, and ensures observability through Prometheus and Grafana.

---

## Collaboration Standards

* *Communication:* Managed via WhatsApp for asynchronous coordination and real-time blocker resolution. 
* *Version Control:* Code was maintained in streakh/Real-Time-Crypto-ML. Development followed a branch-based workflow, with main reserved for tested, production-ready code.
* *Decision-Making:* Strategic decisions (e.g., model selection, API contract changes) were reached by team consensus, with rationale documented in the /docs directory.
* *Conflict Resolution:* Issues were addressed openly. The team prioritized respectful discourse, with escalation to the instructor reserved only for blockers that could not be resolved internally.

---

## Definition of Done (Finalized)

- [x] `docker compose up -d` brings up Kafka, MLflow, the API, ingestor, featurizer, Prometheus, Grafana, and kafka-exporter cleanly
- [x] All four endpoints (`/health`, `/predict`, `/version`, `/metrics`) return valid responses
- [x] 10-minute raw slice replayed end-to-end through Kafka → features → API
- [x] `team_charter.md` and `selection_rationale.md` committed under `docs/`
- [x] Architecture diagram committed to `docs/`
- [x] No secrets committed to the repo (`.env.example` only)
- [x] CI pipeline (Black + Ruff + smoke test) passing
- [x] Grafana dashboard, SLO doc, drift summary, runbook, latency report committed
- [x] `MODEL_VARIANT=ml|baseline` rollback toggle wired through API + compose

---

## Norms

- We have created a WhatsApp group where the primary conversation will take place. All coordination, updates, and blockers should be communicated there.
- Be responsive — a short "on it" or "blocked, need help" goes a long way.
- Don't break `main` — test locally before pushing.
- If the model numbers change, update the model card — don't leave stale metrics in docs.

---

## Operational Norms

* *Transparency:* All AI-assisted development was tracked in docs/genai_appendix.md.
* *Accountability:* The team maintained strict adherence to the project roadmap, ensuring all weekly milestones were met by the assigned deadlines.
* *Documentation:* Technical documentation was kept in sync with the codebase. If model versions or feature schemas changed, the corresponding documentation was updated immediately.
* *Stability:* The team prioritized system stability, ensuring no regression in performance during feature iteration.

---

## Tools & Resources

* *Tech Stack:* Python, Kafka (KRaft), MLflow, Docker.
* *Infrastructure:* GitHub (Repository Management), Docker Compose (Orchestration).
* *Observability:* Prometheus, Grafana, Evidently AI.
* *Data Source:* Coinbase Advanced Trade WebSocket API (BTC-USD ticker).

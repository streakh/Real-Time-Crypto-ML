# Team Charter — Real-Time Crypto Volatility Detection

## Team Members & Roles

| Member | Primary Role | Responsibilities |
|--------|-------------|-----------------|
| Rico Pichardo Abreu  | Model Lead & Improvements | Base model selection, feature engineering improvements, model retraining, handoff folder maintenance |
| Honey Streak | Infrastructure Lead | FastAPI service, Docker Compose setup, Kafka/MLflow containerization, GitHub repo structure |
| Swetaleena Guha | Replay Pipeline & Testing | Run 10-minute slice through the pipeline, validate /predict endpoint end-to-end, write test results |
| Irene John| Docs & Diagrams | team_charter.md, selection_rationale.md, system architecture diagram, model card updates |

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

The project successfully met the following criteria:

- [x] *Deployment:* docker compose up -d successfully initializes the full stack (Kafka, MLflow, API, Ingestor, Featurizer, and the Monitoring stack).
- [x] *API Integrity:* All endpoints (/health, /predict, /version, /metrics) are functional and return expected schemas.
- [x] *Pipeline Verification:* 10-minute replay slice successfully ingested and processed end-to-end.
- [x] *Documentation:* All required documents (team_charter.md, selection_rationale.md, runbook.md, slo.md) are committed.
- [x] *Security:* No secrets were hardcoded; .env.example serves as the configuration template.
- [x] *Quality Assurance:* CI pipeline (Black + Ruff + smoke tests) passes on all PRs.
- [x] *Operational Readiness:* Grafana dashboard, drift monitoring, and MODEL_VARIANT rollback toggles are fully operational.

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

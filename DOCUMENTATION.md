# ATLAS — Complete Documentation Index

Step-by-step documentation of **every phase** of the project — research,
data acquisition, processing (Moon / Earth / Mars), scoring, the app,
validation, reproduction, and compliance with Challenge Guide #09 — lives
in the [`docs/`](docs/) folder:

| # | Document | What it covers |
|---|---|---|
| 00 | [Overview](docs/00_overview.md) | What ATLAS is, the novelty rule, headline results, design principles |
| 01 | [Phase 0 — Research & Data Catalog](docs/01_phase0_research_and_data_catalog.md) | Challenge + guide analysis, coordinate verification (incl. the Shackleton correction), product-by-product coverage matrix, review of the team's first data plan |
| 02 | [Phase 1 — Data Acquisition](docs/02_phase1_data_acquisition.md) | Every file downloaded: source, URL pattern, exact byte size, verification protocol |
| 03 | [Phase 2A — Moon Processing](docs/03_phase2a_moon_processing.md) | PDS3 label parsing, polar-stereographic engine, north-pole handedness discovery, LDSM no-data trap, Diviner temperature — and the final measured profile of all four bases |
| 04 | [Phase 2B — Earth Processing](docs/04_phase2b_earth_processing.md) | The measurement recipe, classic-site control run, novel-site selection rules, the Klyuchevskaya coordinate fix, all 14 discovery measurements |
| 05 | [Phase 2C — Mars Processing](docs/05_phase2c_mars_processing.md) | Jezero Crater from MOLA MEGDR via HTTP range requests |
| 06 | [Phase 3 — Scoring Model](docs/06_phase3_scoring_model.md) | Variables, weights, normalisation, formula, missing-data rule, control-run validation, discovery results, regime clustering, radar plots |
| 07 | [Phase 4 — The App](docs/07_phase4_app.md) | Page-by-page guide incl. the mission presets and live re-weighting system (Guide Objective 6) |
| 08 | [Validation & QA](docs/08_validation_and_qa.md) | The full audit trail: nine verification exercises and the known limitations |
| 09 | [Reproduction Guide](docs/09_reproduction_guide.md) | From-zero rebuild: environment, commands, acceptance numbers, troubleshooting table |
| 10 | [Guide #09 Compliance](docs/10_guide09_compliance.md) | Objective-by-objective compliance matrix and answers to the guide's seven questions |

Related documents:

- [`README.md`](README.md) — project summary and quick start
- [`DATA_DOCUMENTATION.md`](DATA_DOCUMENTATION.md) — dataset-level record
  (v1 team plan → v2 as-built corrections → v3 discovery-run note)
- [`outputs/methodology.md`](outputs/methodology.md) — the in-app
  methodology summary (data, formula, limitations, sources)

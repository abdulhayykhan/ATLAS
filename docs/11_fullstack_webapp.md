# Phase 5 — Full-Stack Web App (`webapp/`)

*Goal: the same science, delivered as a production-style web application —
a **FastAPI** backend exposing the pipeline outputs as a JSON API, and a
**vanilla HTML/CSS/JS** frontend (no frameworks) that is fully responsive
from phones to desktops. The Streamlit app (`src/app.py`) remains in the
repo; the web app is the deployable face of the project.*

---

## Architecture

```
webapp/
├── run.sh                    # one-command start (installs deps if missing)
├── backend/
│   ├── main.py               # FastAPI application (read-only, stateless)
│   └── requirements.txt      # fastapi, uvicorn, pandas, markdown
└── frontend/
    ├── index.html            # single-page app shell (6 views)
    ├── styles.css            # vanilla CSS, mobile-first, 3 breakpoints
    └── app.js                # vanilla JS: routing, fetching, map, radar SVG
```

Data flow: the pipeline (`src/`) precomputes everything into `outputs/`.
The backend loads the four CSVs once (cached), shapes them into API
responses, and serves the frontend + the generated images (`/outputs/*`).
**No science is recomputed in the web layer** except the Guide Objective 6
re-weighting, which deliberately mirrors `src/app.py`'s formula.

Run it:

```bash
bash webapp/run.sh            # http://localhost:8000  (or: run.sh 8080)
# equivalently:
uvicorn webapp.backend.main:app --host 0.0.0.0 --port 8000
```

## Backend API (`webapp/backend/main.py`)

| Endpoint | Returns |
|---|---|
| `GET /api/health` | status + counts (4 bases, 14 sites, 56 score rows) |
| `GET /api/moon-bases` | all base profiles + hillshade URLs |
| `GET /api/earth-sites` | all 14 site profiles incl. `analog_note`, `regime` |
| `GET /api/winners` | official Top-1 novel match per base |
| `GET /api/rankings?base=…&preset=…` | ranking for one base; `preset` ∈ balanced / rover / habitat / isru, or explicit `slope, flat, temperature, soil, relief` weights (0–100) |
| `GET /api/compare?base=…&site=…` | pair score + rank, per-pillar radar similarity (1 − dist; `null` where a pillar was not scored), side-by-side measures |
| `GET /api/mars` | Jezero profile + 3 closest-slope Earth sites |
| `GET /api/methodology` | `outputs/methodology.md` rendered to HTML (tables extension) |
| `GET /api/downloads/{moon,earth,scores}` | the CSVs as file downloads |
| `GET /outputs/*` | generated PNGs/CSVs (hillshades, radars) |
| `GET /` | the frontend (StaticFiles, `html=True`) |

Key behaviours:

- **Official-score guarantee:** with the balanced preset and no explicit
  weights, `/api/rankings` returns the *stored* `analog_score` /
  `rank_for_base` verbatim — the API cannot drift from the published
  Phase 3 ranking. Any other weight set recomputes
  `D = sqrt( Σ w·d² / Σ w )`, `score = 100·exp(−D)` from the stored
  per-pillar distances, with the same missing-pillar renormalisation as
  the model (verified: default → de Gerlache #1 Erebus 72.1; rover preset
  re-ranks live; soil-only custom weights behave per-pillar).
- **JSON hygiene:** NaNs are serialised as `null` (never as invalid JSON
  NaN tokens) via a cleaning pass; the frontend renders `null` as "—" or
  "no data".
- Unknown base/site/preset → proper 404/400 with a message, not a stack
  trace. CORS is open for GET (read-only public data).

## Frontend (`webapp/frontend/`)

Vanilla only: no build step, no framework. Leaflet (CDN) is the single
external library, used for the Finder map, with a graceful fallback
message if it cannot load (the table carries the same data).

Views (hash-routed, one page shown at a time):

1. **Overview** — hero, stat strip (4 bases / 14 sites / 6 terrain types /
   5 repositories / 56 matches), base cards, winner cards, validation note.
2. **Moon Bases** — per-base profile cards with measured-values tables and
   LOLA hillshades, plus the north-pole note.
3. **Analog Finder** — base selector; mission-preset chips; fine-tune
   sliders (debounced live re-ranking via the API); custom-ranking banner
   showing the active weights; Leaflet map with rank-coloured markers and
   metadata popups; ranking table; discovery-notes expander; CSV downloads.
4. **Compare** — any base × site pair: big score, rank, side-by-side
   table, and a **hand-drawn SVG radar chart** (grid rings, axis labels,
   hollow markers + note for unscored pillars).
5. **Mars** — Jezero profile and the three closest-slope Earth sites.
6. **Methodology** — the rendered methodology document.

## Responsive design (`styles.css`)

- **Breakpoints:** ≥1024 px desktop · 720–1023 px tablet · <720 px phone.
- Desktop: multi-column card grids (`auto-fit, minmax`), two-column base
  profiles and compare layout, 5-across stat strip.
- Tablet: 3-across stats, narrower profile split, single-column compare.
- Phone: hamburger navigation (sticky header, collapsible menu); controls
  stack full-width with ≥44 px touch targets; the stat strip goes 2-across;
  the wide ranking **table is replaced by stacked rank cards** (same data,
  no horizontal scrolling); map height reduces to 320 px; base profiles
  and hero type scale via `clamp()`.
- Accessibility touches: semantic landmarks, `aria-expanded` on the menu
  toggle, labelled range outputs, `prefers-reduced-motion` honoured,
  alt text on hillshades, focusable native controls throughout.

## Verification performed

- Backend started under uvicorn; every endpoint exercised with curl:
  health counts (4/14/56), winners match the published scores exactly,
  default ranking returns official values, rover/custom weights re-rank,
  compare returns `soil: null` for Erebus (pillar not scored), Mars
  payload complete, methodology renders, CSV downloads and all static
  assets return HTTP 200, server log clean.
- `node --check` passes on `app.js`; served HTML contains all six views.
- The frontend's data contracts were checked field-by-field against the
  API responses above (no console-only assumptions).

## Deployment notes

- Any host that runs Python: `bash webapp/run.sh` (Render, Railway, a VPS,
  or a container). The app reads only `outputs/` (~5 MB) — the 2.3 GB raw
  data tree is **not** needed at runtime.
- For a static-only demo, the Streamlit app remains available; the web app
  supersedes it for presentation because of the responsive layout and the
  API, which other teams/tools can consume directly.

## Deployment note — Vercel-ready

The web app deploys to **Vercel** with zero configuration: the repo-root
`pyproject.toml` declares the light runtime dependencies (fastapi + markdown)
and `[tool.vercel] entrypoint = "webapp.backend.main:app"`, with the
StaticFiles mounts promoted to the CDN (`cdn = true`). The backend reads the
CSVs with the standard-library `csv` module (no pandas), which keeps the
serverless bundle small; behaviour was re-verified end-to-end in a clean
pandas-free environment after that change. Step-by-step: `docs/12`, §12.3.
Local runs are unchanged (`bash webapp/run.sh`).

## Console redesign (mission-control UI)

The frontend was rebuilt as an operations console in the style of a drone
mission-control interface (dark map canvas, floating glass panels, one orange
and one mint accent, telemetry in DM Mono):

- **Shell:** 60 px icon rail (Overview / Bases / Finder / Compare / Mars /
  Method / Data) + a top telemetry bar (mission, base selector, phase, active
  preset, sites-scored counter, live session clock). On phones the rail becomes
  a bottom tab bar and the console stacks over a 250 px map band.
- **Console (Overview):** the Leaflet map fills the stage (CARTO dark tiles;
  GLOBE toggle switches to Esri satellite imagery). Floating over it: Selected
  Base panel, top-4 Analog Ranking (fleet-style rows with status dots — Best
  match / Ranked / Soil gap), Model Health (per-pillar data coverage x/10 —
  soil reads 8/10 because two sites have no SoilGrids coverage), Mission Log
  (INFO / MISSION / ALERT entries generated from real app events, including the
  soil-gap alerts, with working tab filters), a Site Feed panel (the selected
  base's real LOLA hillshade under a reticle, HUD tapes carrying the #1 site's
  slope and temperature, big analog score), four Moon-base cards, and a map
  legend. Map annotations are real Leaflet layers: orange ring + BEST MATCH
  label on the #1 site, mint ring on the runner-up, dashed rank path through
  the top 3; the initial view fitBounds-pads around the panels so the matches
  sit in the visible corridor.
- **Workspaces:** Bases, Finder, Compare, Mars and Methodology open as one
  large glass panel over the same map. All previous behaviour is preserved:
  presets + custom weight sliders with live re-ranking (shared state between
  console and Finder), expandable discovery notes, radar with hollow markers
  for unscored pillars, CSV downloads.
- **Robustness:** Leaflet 1.9.4 is vendored under `webapp/frontend/vendor/`
  (no CDN dependency); the map-fallback notice appears only after repeated
  tile errors and clears on the next successful tile; zero JS errors and every
  view were verified with headless-Chromium screenshots at desktop and phone
  sizes before this shipped.

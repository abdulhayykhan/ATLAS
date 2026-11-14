# Phase 4 — The ATLAS App (`src/app.py`)

*Goal: a mission planner (or a judge) can explore everything Phases 2–3
produced without touching a terminal. The app reads only the small files in
`outputs/` — it never opens the multi-GB raw rasters — so it starts in
seconds and can be deployed anywhere Streamlit runs.*

Run: `streamlit run src/app.py`

---

## Page 1 — Home

- The question, the four bases, and the novelty rule stated up front:
  classic analogs are excluded by design; the 14 ranked places are new.
- One metric card per base (coordinates, pole, sun %, Earth view %, PSR %).
- The Top-1 novel match per base, from the stored default ranking.

## Page 2 — Moon Bases

Per base: a measured-values table (elevation, slope, flat %, roughness,
PSR %, sun %, Earth %, seasonal mean temperature, winter cold p1) with its
sources line, beside the LOLA hillshade of its ROI. An info box records
that Peary (North Pole) is fully processed — the gap in the team's first
plan — including the northern Diviner tables.

## Page 3 — Earth Analog Finder

- Base selector; **world map** (Folium) with every site as a marker —
  green for #1, blue for top-3, grey otherwise — popups with type, score,
  slope and temperature.
- Ranking table: rank, site, country, terrain type, regime, score, slope,
  flat %, temperature, **seasonal range**, soil percentages.
- **Discovery notes expander:** each site's `analog_note` — why it is a
  *new* candidate — in rank order.
- Downloads: full ranking CSV, Earth profiles CSV, Moon profiles CSV.

### The re-weighting system (Challenge Guide Objective 6)

Guide Objective 6 requires *dynamic parameter re-weighting tailored to
specific hardware/testing profiles*. Implementation:

- **Mission profiles** (preset weight sets):
  | Profile | Slope | Flat | Temp | Soil | Relief | Intent |
  |---|---|---|---|---|---|---|
  | Balanced (team default) | 30 | 20 | 20 | 15 | 15 | the published Phase 3 formula |
  | Rover mobility | 45 | 35 | 5 | 5 | 10 | trafficability first |
  | Habitat & structures | 10 | 35 | 20 | 10 | 25 | buildable, stable ground |
  | Science & ISRU | 15 | 10 | 25 | 35 | 15 | regolith and thermal character |
- **Fine-tune sliders** for all five weights (0–60) under the preset.
- **Live recompute:** when weights differ from the default, the page
  recomputes every score for the selected base from the stored per-pillar
  distances (`D = sqrt( Σ w·d² / Σ w )`, same missing-data renormalisation)
  and re-ranks instantly — no pipeline re-run. A banner states that a
  custom ranking is being shown and which profile produced it; selecting
  Balanced with untouched sliders restores the stored official ranking.

## Page 4 — Compare

Head-to-head for any base × site pair: the pair's Analog Score and rank, a
side-by-side measured-values table (slope, flat %, temperature, relief,
elevation), and — when the site is the base's #1 — its radar plot. A
caption records *why* sun/Earth visibility are absent from the score.

## Page 5 — Mars

Jezero's measured profile (Phase 2C), the three Earth sites whose mean
slope is closest to Jezero's (a first mobility comparison), and the
roadmap sentence: full Mars ranking is future work, labelled as such.

## Page 6 — Methodology & Sources

Renders `outputs/methodology.md` in full: question, data with per-layer
sources, processing (including the orientation and no-data discoveries),
scoring, the discovery design, the validation control run, **answers to the
guide's seven questions**, and the five stated limitations.

## Verification of the app

- Served locally (`streamlit run`, headless) → HTTP 200, clean log.
- **Streamlit AppTest** run over all six pages: zero exceptions, zero
  errors. The Finder test additionally drives the *Rover mobility* preset
  through the UI widgets and re-checks for exceptions — the re-weighting
  path is tested, not just present.
- Compatibility: the app avoids the deprecated `use_container_width`
  argument (removed after 2025-12-31) in favour of `width="stretch"`, so
  it runs on current Streamlit releases without changes.

## Phase 4 exit criteria — all met

- [x] Every Phase 2/3 output reachable through the UI
- [x] Guide Objective 6 implemented as working controls, not a screenshot
- [x] All pages + preset interaction pass automated AppTest with no exceptions
- [x] App depends only on `outputs/` — deployable without the 2.3 GB raw tree

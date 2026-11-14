# ATLAS — Complete Documentation: Overview

**Project:** ATLAS (Analog Terrain & Lunar Alignment System)
**Team:** Binary Knights
**Event:** NASA International Space Apps Challenge 2026 — local event challenge guide **#09**
**Challenge:** *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*
**Repository:** https://github.com/abdulhayykhan/ATLAS

---

## 1. What ATLAS is

ATLAS is a working discovery engine that answers one question with real data:

> *Which places on Earth are most similar to the four planned permanent Moon
> base sites — Peary, Shackleton, de Gerlache and Amundsen — so that rovers,
> habitats and crews can be tested and trained there first?*

It does this in four measured steps, with no hand-entered "facts" about any
site anywhere in the pipeline:

1. **Measure the Moon.** All four base sites are measured directly from NASA
   Lunar Reconnaissance Orbiter (LRO) data: LOLA topography, LPSR shadow
   masks, PGDA-69 illumination models and Diviner temperature tables — for
   **both** lunar poles.
2. **Measure the Earth.** Candidate terrestrial sites are measured from
   Copernicus DEM GLO-30 terrain, NASA POWER temperature climatology and
   SoilGrids 2.0 soil data, using identical statistics (mean slope, flat-area
   fraction, relief, temperature).
3. **Score and rank.** A published, weighted dissimilarity formula compares
   every Earth site against every Moon base (56 pairs in the discovery run),
   producing an Analog Score and a per-base ranking, plus K-Means regime
   clustering of the Earth sites.
4. **Explore.** A six-page Streamlit app presents the bases, the rankings on
   a world map, head-to-head comparisons, a Mars quick-look, and the full
   methodology — including mission-specific re-weighting controls that let a
   planner re-rank sites live for rover, habitat or science priorities.

A Mars quick-look (Jezero Crater from MOLA data) runs through the same
terrain method to show the pipeline is body-agnostic.

## 2. The novelty rule (Challenge Guide #09)

The local event's Challenge Guide #09 states the task's core explicitly:
participants must **discover, characterize and formally rank *novel*
terrestrial testing analogs**. Its Background section names the world-renowned
sites — the Atacama Desert, Mauna Loa, Haughton Crater — as the small,
already-documented fraction of Earth's extreme landscapes.

ATLAS therefore runs in two stages (details in `04_phase2b_earth_processing.md`
and `06_phase3_scoring_model.md`):

- **Stage 1 — validation control run.** The engine was first run on the
  classic catalogued analogs (Atacama, McMurdo Dry Valleys, Haughton,
  Rio Tinto, Mauna Kea, Meteor Crater, Iceland, Svalbard). Untuned, it ranked
  McMurdo #1 for three of the four bases and Atacama #1 for Peary — the
  literature's own answers. This proves the scoring measures something real.
- **Stage 2 — discovery run (the shipped results).** All classic sites are
  then excluded, and 14 lesser-known candidate places across six terrain
  types are profiled and ranked instead. These are ATLAS's discoveries.

## 3. Headline results (discovery run)

| Moon base | #1 novel analog | Score | #2 | #3 |
|---|---|---|---|---|
| Shackleton | Klyuchevskaya Volcanic Group, Kamchatka | **69.7** | Mount Erebus (67.4) | Deception Island (59.8) |
| de Gerlache | Mount Erebus, Antarctica | **72.1** | Klyuchevskaya (69.5) | Deception Island (65.8) |
| Peary | Elgygytgyn Crater, Chukotka | **63.1** | Lut Desert (61.5) | Qaidam Basin (61.5) |
| Amundsen | Mount Erebus, Antarctica | **62.7** | Klyuchevskaya (60.4) | Badain Jaran Desert (56.1) |

72.1 (de Gerlache ↔ Mount Erebus) is the highest score anywhere in the
project — higher than any classic site scored in the control run.

## 4. Documentation map

| File | Contents |
|---|---|
| `01_phase0_research_and_data_catalog.md` | Challenge analysis, dataset research, product-by-product coverage decisions, review of the team's first data plan |
| `02_phase1_data_acquisition.md` | Every download: source, URL pattern, exact file, size, verification |
| `03_phase2a_moon_processing.md` | PDS label parsing, polar-stereographic engine, orientation discovery, all four base profiles step by step |
| `04_phase2b_earth_processing.md` | Site-selection rules, terrain/temperature/soil pipelines, the classic control run and the novel discovery run |
| `05_phase2c_mars_processing.md` | Jezero Crater from MOLA MEGDR via HTTP range requests |
| `06_phase3_scoring_model.md` | Normalisation, weights, formula, missing-data rule, clustering, radar plots, full results tables |
| `07_phase4_app.md` | The Streamlit app page by page, including the live re-weighting system |
| `08_validation_and_qa.md` | Every verification performed, with the evidence for each |
| `09_reproduction_guide.md` | From-zero reproduction: environment, commands, expected outputs, troubleshooting |
| `10_guide09_compliance.md` | Objective-by-objective compliance with Challenge Guide #09 and answers to its seven questions |

The shorter `outputs/methodology.md` is the in-app summary of the same
material; `DATA_DOCUMENTATION.md` is the dataset-level record (v1 plan,
v2 as-built corrections, v3 discovery-run note).

## 5. Design principles followed throughout

1. **Measured, never asserted.** Every number in the outputs comes from a
   named dataset read by code in `src/`. If a value could not be measured,
   it is recorded as missing (NaN) — never estimated, never filled with a
   plausible-looking number.
2. **Missing data is not a score.** Where a dataset does not cover a site
   (SoilGrids in Antarctica, the salt crust of Etosha Pan), the scoring
   pillar is dropped for that site and the remaining weights renormalised.
3. **Fix the data before the model.** Three of the project's most important
   results are data corrections, not modelling choices: the north-pole grid
   handedness, the LDSM no-data trap, and Shackleton's IAU centre.
4. **Publish the formula and the limitations with the results.** Weights,
   normalisation and every known limitation are in the app itself, not in a
   separate report a judge might never open.

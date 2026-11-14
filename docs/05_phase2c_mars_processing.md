# Phase 2C — Mars Quick-Look (`src/preprocess_mars.py`)

*Goal: prove the terrain method is body-agnostic by measuring a Mars site
the same way the Moon bases were measured. Output:
`outputs/mars_profiles.csv`. Runtime ≈5 seconds; bytes downloaded ≈3 MB.*

---

## Step 2C.1 — Route selection (two servers, one answer)

1. **USGS planetary map mosaic server** — tried first for a MOLA blended
   DEM window. It returns **HTTP 403 to scripted/GDAL access**. Recorded as
   a dead end; not retried, not worked around with spoofing.
2. **NASA PDS MOLA MEGDR** — the Mission Experiment Gridded Data Record
   tiles are plain binary grids with published geometry, ideal for the
   range-request technique below.

## Step 2C.2 — Target and tile

- Target: **Jezero Crater** (18.44° N, 77.45° E) — Perseverance's landing
  site, the natural Mars counterpart to a "future base" study area.
- Tile: `megt44n000hb` — covers latitude 0–44° N, longitude 0–90° E at
  128 pixels/degree, big-endian int16, one row = 23,040 bytes. Jezero falls
  inside it; no other tile is touched.

## Step 2C.3 — Windowed read by HTTP range requests

Instead of downloading the ~130 MB tile:

1. Compute the pixel window for a ~20 km study area from the tile geometry
   (128 px/°; row 0 at the tile's northern edge).
2. Issue one HTTP **Range** request per needed row-band covering the
   window's byte span.
3. Parse the returned bytes as big-endian int16 elevations (MOLA areoid
   metres) in memory.

Total transferred ≈3 MB. The same pattern — *read the window, not the
planet* — is what SoilGrids subsetting does on the Earth side.

## Step 2C.4 — Statistics (identical recipe to Phases 2A/2B)

Slope from DEM gradients at the tile's true ground resolution (≈463 m/px
at the equator, cos-latitude corrected); then mean elevation, relief (std),
mean slope, % of pixels < 5° and < 10°.

## Step 2C.5 — Result

| Region | Elev mean (m) | Relief (m) | Slope (°) | <5° (%) | <10° (%) |
|---|---|---|---|---|---|
| Jezero Crater | −2440.9 | 229.4 | 2.92 | 82.4 | 93.1 |

A flat-floored crater: 93.1% of the study area is flatter than 10° — the
quantitative version of why Jezero was landable. In the app's Mars page,
Earth sites are ranked by slope-gap to Jezero as a first mobility
comparison.

## Step 2C.6 — Scope honesty

This is a **quick-look**, labelled as such everywhere it appears: one Mars
region, terrain only. A full Mars ranking (multiple regions; THEMIS-derived
temperature and thermal inertia) is the documented roadmap item, not a
hidden gap — see Limitations in `outputs/methodology.md`.

## Phase 2C exit criteria — all met

- [x] Real Mars data measured with the project's own method
- [x] No bulk download; access method documented incl. the 403 dead end
- [x] Result cross-checks against Jezero's known character (flat floor)

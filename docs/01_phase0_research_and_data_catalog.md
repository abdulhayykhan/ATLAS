# Phase 0 — Research, Challenge Analysis and Data Catalog

*Goal of this phase: understand exactly what the challenge asks, find every
dataset that could answer it, and record — before writing any processing
code — which product covers which base, at what resolution, with what traps.*

---

## Step 0.1 — Read the challenge from the primary source

The challenge page (*Identify Earth Locations that Analog the Permanent Moon
Base Locations and Mars*, Intermediate, Earth/Moon/Mars) was read in full.
Extracted requirements:

- The four target bases are the craters **Peary, Shackleton, de Gerlache and
  Amundsen**, selected by NASA for water-ice access in permanently shadowed
  regions (PSRs), favourable lighting, and science value.
- Comparison variables named by the challenge: **slope, temperature,
  sun visibility %, Earth visibility %, soil type, geological composition,
  thermal properties**.
- Expected tool features (any of): layered maps, querying/comparing across
  remote-sensing datasets, radar-plot comparison, a **dissimilarity score**,
  downloads (GeoTIFF/CSV/shapefile), a source cited for every layer.
- Named resource families: NASA Earthdata, Worldview, Planetary Data System
  (PDS), LRO LOLA, LRO Diviner; plus RADARSAT/RCM, Copernicus, ESA, JAXA.

## Step 0.2 — Read the local event guide (Challenge Guide #09)

The Cedar College (Karachi) local-event guide for this challenge (13 pages)
was read in full. It adds the decisive framing used by the whole project:

- **Introduction:** the task is to *"discover, characterize, and formally
  rank **novel** terrestrial testing analogs"* — Earth's extreme deserts,
  volcanic fields, salt flats, permafrost basins and cave systems *"remain
  systematically uncharacterized against standardized, multi-variable
  planetary benchmarks."*
- **Background:** world-renowned analogs (Atacama, Mauna Loa, Haughton) are
  well documented but *"represent only a fraction"*; the bottleneck is the
  lack of an *automated discovery engine* for uncatalogued grounds.
- **Six objectives with target benchmarks** — reproduced and answered in
  `10_guide09_compliance.md`. The load-bearing ones: integrate ≥3 open
  repositories; index ≥4 unique terrain types (arid basins, high-altitude
  volcanic fields, salt flats, subterranean caves); multi-variable scoring
  including thermal and seasonal behaviour; **dynamic re-weighting for
  mission-specific testing profiles**.
- **Section 7** lists seven questions a solution should be able to answer
  (illumination geometry, volatile-trap data layers, resolution
  normalisation, distance metrics/clustering, subsurface data, dynamic
  re-weighting, validation). ATLAS's answers are in
  `10_guide09_compliance.md` and in the in-app methodology.

**Decision recorded:** the famous analog sites are *context and validation
material*, not the deliverable. The deliverable is a ranked set of new sites.

## Step 0.3 — Verify the four bases' coordinates from authoritative sources

Coordinates were not taken from the challenge page's prose; each base was
checked against IAU/Wikipedia and the mission literature:

| Base | Pole | Centre used | Diameter | Note |
|---|---|---|---|---|
| Peary | N | **88.63° N, 24.4° E** | 79 km | Older sources give 33° E; immaterial inside a 40 km ROI, 24.4° E is the current IAU-consistent value |
| Shackleton | S | **89.67° S, 129.78° E** | 21 km | **Corrected during the build** — see Step 0.3.1 |
| de Gerlache | S | 88.5° S, 87.1° W | 32 km | |
| Amundsen | S | 84.5° S, 82.8° E | 103 km | Lies **outside** the popular 87–90° S mosaic (Step 0.4) |

### Step 0.3.1 — The Shackleton correction (found in Phase 2, recorded here)

Many secondary sources quote Shackleton as "89.9° S, 0° E". That is not its
centre: the crater centre is ~10 km from the pole at 89.67° S, 129.78° E,
with the pole on its rim. The error was caught visually — a hillshade built
around (89.9, 0) showed the crater bowl displaced ~5–7 km from frame centre —
and confirmed against IAU/Wikipedia values (89.67° S, 129.7° E; LPSC site
studies ~89.6° S, 131° E). After correction the crater sits dead-centre in
its hillshade and its measured PSR fraction rose from 24.7% to 33.3%,
consistent with a shadow-dominated crater interior. Any project quoting
"89.9° S, 0° E" is profiling a point on Shackleton's outer flank.

## Step 0.4 — Moon data: product-by-product coverage research

The team's initial preference was **PGDA Product 81** (South Pole LOLA DEM
Mosaic, Barker et al. 2021): 5 m/px GeoTIFFs over 87–90° S (LDEM 3.3 GB,
LDSM slope 4.9 GB, hillshade 820 MB, LDEC 140 MB). It was verified live on
the PGDA site — and found to have three disqualifying limits for this
challenge:

1. **South pole only** — Peary (North Pole) does not exist in it.
2. **Amundsen is outside it** (84.5° S < 87° S).
3. **Topography only** — no temperature, no illumination, no PSR products.

The full catalog research (every product checked on its live PGDA/PDS page)
produced the coverage matrix the build actually used:

| Need | Product chosen | Coverage / resolution | Why |
|---|---|---|---|
| Terrain, South | PDS LOLA GDR polar grids: LDEM 80S 80 m, LDSM 75S 240 m, LDRM 75S 240 m | to 75° S | Authoritative PDS IMG+LBL; Amundsen included; no 9 GB mosaic needed |
| Terrain, North | Same set, 80N / 75N | to 75° N | The only way to cover Peary in the same system |
| Ready-made rim sites (cross-check) | PGDA 78 (Site04 Shackleton Rim, Site11 de Gerlache Rim) | 5 m | Used as documentation cross-reference, not the pipeline input |
| Wide-area south DEM (alternative) | PGDA 90 (Barker 2023, COG) | 80S 20 m | Noted as fallback for Amundsen |
| North high-res context | PGDA 98 (Barker 2025) | 83N 10 m finest | There is **no** northern equivalent of the 5 m mosaic — recorded so nobody promises one |
| Illumination + Earth visibility + PSR source science | **PGDA 69** (Mazarico et al. 2011) | 240 m (65–90°), 120 m (75–90°), 60 m (85–90°); 18.6-year hourly averages | The challenge's sun % and Earth % exist only here |
| PSR masks | LPSR 81S / 81N, 240 m (PDS extras) | both poles | Binary permanent-shadow masks |
| Temperature | **Diviner PCP** polar tables (Williams et al. 2019), pols **and** poln, solar-longitude slices 01 (winter) + 48 (opposite season) | polar stereographic bins | The only Diviner product family that actually contains the poles (Step 0.6) |

Deliverable of this step: `SpaceApps_2026_Dataset_Catalog_Organized.xlsx`
(9 sheets: README, COVERAGE_MATRIX, MOON_SOUTH, MOON_NORTH,
MOON_TEMP_ILLUM, EARTH_ANALOG, EARTH_SITES, MARS, DOWNLOAD_PLAN — every row
with source, coverage, resolution, exact filenames, sizes, links, priority,
use, warnings, citation) plus a Word summary. The catalog lives in the team's
working files; its conclusions are baked into `src/` and
`DATA_DOCUMENTATION.md`.

## Step 0.5 — Earth and Mars data research

| Need | Chosen source | Rejected / caveated alternatives |
|---|---|---|
| Earth terrain | **Copernicus DEM GLO-30** (ESA, AWS Open Data COGs, 30 m) | SRTM/NASADEM: **no coverage of Iceland's interior or Antarctica** — recorded as a warning; ETOPO at 0.05° (≈5.6 km) kept only as the team's future global-scan layer because a 1.2 km crater is smaller than one of its pixels |
| Earth temperature | **NASA POWER** climatology API (monthly T2M, no key) | MODIS LST noted for the future scan; POWER gives the seasonal range the guide's Objective 5 needs |
| Earth soil | **SoilGrids 2.0** (ISRIC) 0–5 cm sand/clay/coarse fragments via VRT/WCS subsetting | **Never download globally** (hundreds of GB) — subset per site box only; **no Antarctica coverage** (discovered in Phase 2) |
| Mars terrain | **MGS MOLA MEGDR** (PDS) | USGS mosaic server (blocks scripted access — Phase 2C) |

## Step 0.6 — Review of the team's first data plan (DATA_DOCUMENTATION v1)

A teammate's data document (PDS/ODE route, ~3.14 GB, <8 GB RAM design) was
reviewed line by line against the challenge before building. Good parts kept:
label/manifest hygiene, the PCP seasonal-extremes idea, land-cover masking
as a future scan step. Three must-fix findings, all later confirmed in the
build:

1. **South Pole only** — Peary and the entire north missing.
2. **~830 MB of its Diviner files are unusable at the bases**: the
   cylindrical soil-temperature (630 MB) and rock-abundance (199 MB) maps
   span only −60°…+60° latitude; none of the four polar bases exists in
   them. Its PCP polar files were the correct ones.
3. **No illumination data at all**, despite the challenge requiring sun %
   and Earth % (fixed by PGDA 69).

Should-fix findings: ETOPO 5.6 km Earth grid too coarse (→ Copernicus
second stage); one pooled South-Pole vector instead of per-base profiles;
an alignment matrix that conflated rock abundance/PSR with emissivity/land
cover; Mars absent.

## Phase 0 exit criteria — all met

- [x] Challenge + local guide read from primary sources
- [x] Base coordinates verified (one correction found)
- [x] A named product for every required variable, both poles
- [x] Every product's coverage trap written down *before* downloading
- [x] Team data plan reviewed; fatal gaps identified and fixed on paper

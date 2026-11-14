# Phase 2B — Earth Processing (`src/preprocess_earth.py`)

*Goal: profile candidate Earth sites with the same statistics used for the
Moon, so Phase 3 compares measurements with measurements. Output:
`outputs/earth_profiles.csv`. The phase ran twice: a classic-site control
run (validation) and the novel-site discovery run (the shipped results).*

---

## Step 2B.1 — The measurement recipe (identical for every site)

Each site is a fixed **20 × 20 km box** centred on the site coordinates
(`box_bounds`: ±10 km converted with 111.32 km/° latitude and
cos-latitude-corrected longitude). Three independent sources per site:

### (a) Terrain — Copernicus DEM GLO-30 (30 m)

- Open the site's 1° tile (local file if present, else the AWS COG URL).
- Read the box window at native resolution.
- Slope from **Horn-style gradients** of the DEM itself, with true pixel
  size in metres (Δx corrected by cos φ — essential at polar latitudes,
  where a degree of longitude is a fraction of its equatorial length):
  `slope = atan( sqrt(gx² + gy²) )`.
- Statistics: elevation mean/median/std (relief)/min/max; slope
  mean/median; % of pixels < 5° and < 10°.
- **Water masking (island/coastal sites only):** where a box includes sea
  (Mount Erebus, Deception Island, Jeju), pixels at DEM elevation ≤ 0.5 m
  are excluded — Copernicus encodes sea as 0, and unmasked ocean would
  fabricate "flatness". The flag is per-site and recorded in the code.

Why 30 m matters: the team's first design resampled Earth to a 0.05°
(≈5.6 km) ETOPO grid. At that size Meteor Crater (~1.2 km) is smaller than
one pixel and no slope statistic is comparable to the Moon's 240 m product.
The 30 m stage is what makes the comparison honest; the coarse grid remains
documented as the future *global scan* layer only.

### (b) Temperature — NASA POWER climatology API

`GET https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M&community=RE&longitude=…&latitude=…&format=JSON`
(no key). Recorded: annual mean, coldest month, warmest month, and
**seasonal range** (warmest − coldest month) — the variable that carries
Challenge Guide Objective 5 (seasonal dynamics / freeze–thaw) into the
dataset. Values are 2 m air-temperature climatology; the Moon side is
surface bolometric temperature, and the methodology states plainly that the
two are compared as thermal-regime indicators (Limitation 3).

### (c) Soil — SoilGrids 2.0 (ISRIC), streamed per box

- Properties: `sand`, `clay`, `cfvo` (coarse fragments), 0–5 cm mean, from
  the public VRT service (`files.isric.org/soilgrids/latest/data/<prop>/…`).
- The site box is transformed from EPSG:4326 into SoilGrids' Interrupted
  Goode Homolosine CRS before windowing (`transform_bounds`) — skipping
  this step reads the wrong part of the planet.
- Environment quirk: the VRT service requires
  `GDAL_HTTP_UNSAFESSL="YES"` through this network's proxy; values are
  stored ×10 and divided back to %.
- Each property read takes ~20–70 s (remote tiles); the full pool was run
  in three parallel chunks using the script's subset arguments
  (`preprocess_earth.py <data> <indices> <part_file>`) and merged in
  site-list order.
- **Two coverage gaps found, both handled by the missing-data rule:**
  *SoilGrids does not cover Antarctica at all* (Erebus, Deception Island →
  NaN), and the salt crust of Etosha Pan returns no valid pixels (→ NaN).
  In Phase 3 those sites' soil pillar is dropped and weights renormalised —
  missing data is never scored as zero.

## Step 2B.2 — Control run: the classic sites (validation only)

First execution used the eight classic analog candidates — Atacama,
McMurdo Dry Valleys, Haughton Crater, Iceland Volcanic Fields, Meteor
Crater, Rio Tinto, Mauna Kea, Svalbard (Adventdalen) — with these tiles:

```
S24_00_W070_00  S78_00_E162_00  N75_00_W090_00  N64_00_W020_00
N35_00_W112_00  N37_00_W007_00  N19_00_W156_00  N78_00_E015_00
```

Purpose: **engine validation**, per the guide's Question 7. Fed into
Phase 3 unchanged, the engine ranked McMurdo Dry Valleys #1 for
Shackleton (65.5), de Gerlache (70.2) and Amundsen (59.2), and Atacama #1
for Peary (64.3) — the established literature answers, produced by an
untuned formula. This control is also what exposed the SoilGrids
Antarctica gap in its original form (McMurdo's soil NaN initially acted as
a penalty; the renormalisation rule exists because of this run).

The classic sites are **not** in the shipped results. They are the control
group, and the shipped code keeps their names only in
`CLASSIC_SITES_EXCLUDED`, as documentation.

## Step 2B.3 — Discovery run: selecting 14 novel sites

Selection rules (applied before any measurement):

1. **Exclude** every site in, or directly named by, the classic catalogues
   and the guide's own "already documented" examples: Atacama, Mauna
   Loa / Mauna Kea and Hawaii generally, Haughton, Rio Tinto, Iceland,
   Mojave, McMurdo, Meteor Crater, Svalbard, Wadi Rum, Pilbara.
2. **Span at least four of the guide's terrain types** — the pool covers
   six: arid basins, salt flats, volcanic fields, subterranean caves,
   permafrost terrain, impact structures.
3. **Every site must be measurable** by the Step 2B.1 recipe (a Copernicus
   tile, a POWER point, a SoilGrids box or a documented gap).
4. **Coordinates are study-box centres** chosen on the named feature and
   verified against the DEM itself where the feature has a sharp signature
   (Step 2B.4).

The pool (full per-site rationale is in each record's `analog_note`):

| # | Site | Country | Centre | Terrain type |
|---|---|---|---|---|
| 1 | Lut Desert (Dasht-e Lut) | Iran | 30.60, 58.70 | Arid basin |
| 2 | Qaidam Basin | China | 37.40, 94.30 | Arid basin |
| 3 | Badain Jaran Desert | China | 40.10, 102.20 | Arid basin |
| 4 | Etosha Pan | Namibia | −18.80, 16.30 | Salt flat |
| 5 | Salinas Grandes | Argentina | −30.00, −65.80 | Salt flat |
| 6 | Mount Erebus | Antarctica | −77.53, 167.17 | Volcanic field |
| 7 | Deception Island | Antarctica | −62.97, −60.70 | Volcanic field |
| 8 | Klyuchevskaya Volcanic Group | Russia | 56.06, 160.64 | Volcanic field |
| 9 | Undara Lava Tubes | Australia | −18.20, 144.60 | Subterranean cave |
| 10 | Manjanggul Lava Tube (Jeju) | South Korea | 33.47, 126.77 | Subterranean cave |
| 11 | Yamal Peninsula (Bovanenkovo) | Russia | 70.40, 68.50 | Permafrost terrain |
| 12 | Elgygytgyn Crater | Russia | 67.50, 172.08 | Impact structure |
| 13 | Lonar Crater | India | 19.98, 76.51 | Impact structure |
| 14 | Tenoumer Crater | Mauritania | 22.92, −10.40 | Impact structure |

**Cave-site method note:** a surface DEM cannot measure a cave interior,
and ATLAS does not pretend otherwise. Cave sites are profiled by their
surface box (the volcanic host terrain a field team would actually work
in) and carry their documented cave systems as metadata — Undara's ~160 km
of lava tubes, Manjanggul's 7.4 km multi-level tube. Subterranean LiDAR
surveys are a declared roadmap item (Guide Q5).

## Step 2B.4 — The Klyuchevskaya coordinate correction

The first Klyuchevskaya profile was physically impossible for Eurasia's
tallest volcano: mean elevation 51.9 m, 97.2% of the box flatter than 10°.
Diagnosis from the DEM itself: the full tile's maximum is 4,846 m, but it
sits at **56.058° N**, not the 56.65° N centre taken from memory — half a
degree south. The centre was corrected to the DEM-verified summit
(56.06, 160.64) and the site re-run alone: elevation mean 2,347.7 m,
max 4,845.6 m, mean slope 18.44°. (That correction is why Klyuchevskaya
could become Shackleton's #1 match in Phase 3.) Lesson encoded in the
process: *a profile that contradicts the feature it names is a bug report,
not a result.*

## Step 2B.5 — Discovery-run measurements (all 14 sites)

| Site | Elev mean (m) | Relief (m) | Slope (°) | <10° (%) | Temp (°C) | Seasonal range (°C) | Sand/Clay/CF (%) |
|---|---|---|---|---|---|---|---|
| Lut Desert | 304.8 | 85.1 | 3.25 | 93.8 | 26.2 | 25.4 | 60.9 / 17.4 / 21.6 |
| Qaidam Basin | 2714.7 | 16.9 | 1.41 | 99.2 | 5.9 | 28.2 | 48.5 / 17.2 / 22.0 |
| Badain Jaran | 1311.0 | 69.7 | 13.09 | 39.5 | 9.0 | 35.3 | 33.2 / 26.0 / 22.2 |
| Etosha Pan | 1080.9 | 0.7 | 0.43 | 100.0 | 23.9 | 10.9 | — (no valid pixels) |
| Salinas Grandes | 310.0 | 60.9 | 1.50 | 99.2 | 21.6 | 16.8 | 58.1 / 13.0 / 4.6 |
| Mount Erebus | 1801.1 | 751.3 | 14.83 | 33.5 | −19.4 | 22.6 | — (Antarctica) |
| Deception Island | 118.5 | 78.1 | 11.85 | 18.3 | −1.9 | 6.5 | — (Antarctica) |
| Klyuchevskaya | 2347.7 | 784.6 | 18.44 | 25.4 | −5.5 | 27.4 | 52.6 / 16.2 / 17.6 |
| Undara | 733.2 | 70.6 | 2.67 | 96.7 | 23.6 | 8.7 | 47.9 / 32.7 / 7.2 |
| Manjanggul (Jeju) | 182.8 | 123.0 | 4.56 | 86.4 | 16.3 | 20.0 | 33.0 / 29.6 / 9.7 |
| Yamal Peninsula | 7.8 | 8.3 | 1.18 | 99.8 | −7.0 | 31.9 | 43.8 / 20.5 / 7.7 |
| Elgygytgyn Crater | 527.0 | 55.1 | 5.21 | 80.8 | −10.7 | 38.4 | 33.0 / 23.6 / 14.6 |
| Lonar Crater | 542.3 | 22.8 | 2.21 | 98.9 | 26.0 | 13.2 | 24.8 / 47.9 / 20.0 |
| Tenoumer Crater | 258.7 | 7.2 | 0.96 | 99.6 | 26.1 | 19.9 | 49.9 / 25.5 / 27.6 |

Spot-readings that confirm the pipeline sees the real places: Etosha's
relief is 0.7 m across 20 km (a pan, exactly); Yamal's mean elevation is
7.8 m (low tundra plain); Elgygytgyn has the pool's largest seasonal range,
38.4 °C (deep continental Arctic); Deception is the steepest low site
(only 18.3% flatter than 10° — a caldera's walls, with the sea masked out).

## Phase 2B exit criteria — all met

- [x] Identical statistic recipe for every site; sources cited per row
- [x] Control run completed and archived as validation evidence
- [x] Discovery pool: 14 sites, 6 terrain types, zero classic sites
- [x] Coverage gaps (Antarctica soil, Etosha soil) recorded as NaN, not filled
- [x] Every implausible profile investigated to a root cause before use

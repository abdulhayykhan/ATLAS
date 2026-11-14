# ATLAS — Methodology

## Question
Which locations on Earth are most similar to the four planned permanent Moon
base sites — **Peary, Shackleton, de Gerlache, Amundsen** — so that equipment,
rovers and crews can be tested and trained there first?

## Data (all real, all cited per layer in the app)
**Moon — NASA Lunar Reconnaissance Orbiter:**
- Topography: LOLA gridded records (PDS) — LDEM 80 m elevation, LDSM 240 m
  slope, LDRM 240 m roughness, for **both** poles (80S/75S and 80N/75N).
- Shadow: LPSR permanently-shadowed-region masks (81S and 81N).
- Light: PGDA Product 69 average solar visibility and average Earth
  visibility maps (Mazarico et al. 2011), 60 m sets at the poles and the
  120 m 75S set for Amundsen; values are averages over the 18.6-year cycle.
- Temperature: Diviner Polar Cumulative Products (Williams et al. 2019) —
  polar-south (pols) and polar-north (poln) bolometric temperature tables,
  winter solar-longitude slice 01 and opposite-season slice 48.

**Earth:**
- Terrain: Copernicus DEM GLO-30 (ESA, 30 m) — slope computed with Horn
  gradients at native resolution inside a fixed 20 × 20 km box per site.
- Temperature: NASA POWER climatology (NASA LaRC) monthly 2 m air
  temperature at each site.
- Soil: SoilGrids 2.0 (ISRIC) 0–5 cm sand, clay and coarse fragments.

**Mars (quick-look):** MGS MOLA MEGDR topography (PDS), Jezero Crater window.

## Processing
- PDS IMG files are read directly from their detached labels (lines,
  samples, scaling factor, offset, map-projection offsets) and converted
  from planetocentric lat/lon to polar-stereographic pixels with the
  spherical, true-at-pole formula. The orientation convention was validated
  against named craters (south: Amundsen, Shoemaker, Faustini, Haworth,
  Sverdrup, de Gerlache; north: Rozhdestvenskiy and its satellites, Byrd,
  Sylvester, Peary) whose floors must land on local elevation lows. The
  north-pole grids are stored with the opposite row handedness to the
  south-pole grids; using the southern convention at the north pole would
  silently mirror every location (Peary's profile changes completely when
  this is corrected — its floor is deep and flat, as published).
- LDSM note: DN = 0 in the slope product is a no-data marker, not 45°
  (verified: DN-0 pixels have ordinary ~10° DEM-gradient slopes). All slope
  statistics exclude DN 0.
- Study areas: circular regions of interest — Shackleton 15 km, de Gerlache
  20 km, Peary 40 km, Amundsen 60 km radius; Earth sites use 20 × 20 km boxes.

## Scoring
1. Variables: mean slope, % area with slope < 10°, mean temperature,
   relief (elevation standard deviation), soil/regolith proxy.
2. Each variable is min–max normalised to 0–1 across the Moon bases and
   Earth sites together.
3. Dissimilarity D = weighted Euclidean distance with weights
   **slope 30%, flat area 20%, temperature 20%, soil 15%, relief 15%**.
4. **Analog Score = 100 · exp(−D)** (100 = identical). Sites are ranked per base.
5. Soil: no dataset gives lunar soil percentages at these sites, so the soil
   pillar is an Earth-side *regolith-likeness* score (coarse fragments +
   sand − clay, normalised), the same for every base and labelled a proxy.
   SoilGrids does not cover Antarctica, so McMurdo Dry Valleys has no soil
   values; for that site the soil pillar is dropped and the remaining
   weights renormalised — missing data is never scored as zero.
6. Sun visibility % and Earth visibility % are **not** scored — Earth has no
   counterpart. They are displayed as mission context.

## Benchmark check
McMurdo Dry Valleys, Antarctica — the literature's classic lunar analog —
ranks **#1 for three of the four bases** (Shackleton, de Gerlache,
Amundsen), and the Atacama Desert, the classic hyper-arid analog, ranks #1
for Peary. The engine was not tuned to produce this; it follows from the
measurements and the stated weights.

## Limitations (stated, not hidden)
1. **Temperature gap:** no Earth location is as cold as the lunar polar
   surface (seasonal means below −150 °C). Absolute-temperature comparison
   therefore compresses all scores; rankings within a base stay meaningful.
2. **Resolution mismatch:** Moon slope is measured at 240 m baseline, Earth
   slope at 30 m. Fine Earth detail raises Earth slope slightly relative to
   the Moon; the comparison is conservative, not exact.
3. **Air vs surface:** Earth temperature is 2 m air climatology; Moon
   temperature is surface bolometric temperature. They are compared as
   thermal-regime indicators, not identical physical quantities.
4. **Candidate set:** eight well-known analog candidate sites are profiled;
   a full global scan (the team's ETOPO/MODIS design) is the next step.
5. Diviner soil-temperature and rock-abundance *cylindrical* maps cover only
   −60°…+60° latitude and therefore contain **no data at any of the four
   polar bases**; they are not used. Polar (PCP) products are used instead.

## Sources
- NASA PDS Geosciences Node — LRO LOLA GDR, LPSR, Diviner PCP:
  pds-geosciences.wustl.edu
- PGDA Product 69 (Lunar Polar Illumination) & LOLA team (imbrium.mit.edu)
- Copernicus DEM GLO-30 © ESA / Copernicus, AWS Open Data
- NASA POWER — power.larc.nasa.gov
- SoilGrids 2.0 © ISRIC — soilgrids.org (CC BY 4.0)
- NASA PDS — MGS MOLA MEGDR (Jezero window)

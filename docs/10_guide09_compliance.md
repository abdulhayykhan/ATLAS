# Challenge Guide #09 — Compliance Matrix and Judge Questions

*The local event's Challenge Guide #09 defines six objectives with target
benchmarks (its Section 6) and seven questions a solution should answer
(its Section 7). This file maps ATLAS to both, with evidence locations.
Where ATLAS does not meet a point, it says so — the same statements appear
in the app's methodology, so nothing here is a claim the product doesn't
make about itself.*

---

## Part A — The six objectives

### Objective 1 — Cross-Domain Data Correlation
*Benchmark: integrate at least 3 distinct open data repositories.*
**Met — 5 repositories.** NASA PDS (LOLA GDR, LPSR, Diviner PCP, MOLA
MEGDR), NASA PGDA (Product 69 illumination), ESA Copernicus (DEM GLO-30),
NASA POWER (climatology API), ISRIC SoilGrids 2.0. All are ingested
programmatically by `src/`; every layer's source is cited in the outputs
and app. → `01`, `02`

### Objective 2 — Geographical Scope
*Benchmark: map and index at least 4 unique terrain types (arid basins,
high-altitude volcanic fields, salt flats, subterranean caves).*
**Met — 6 terrain types, 14 sites.** Arid basins (Lut, Qaidam, Badain
Jaran), salt flats (Etosha, Salinas Grandes), volcanic fields (Erebus,
Deception Island, Klyuchevskaya), subterranean caves (Undara, Manjanggul),
plus permafrost terrain (Yamal) and impact structures (Elgygytgyn, Lonar,
Tenoumer). Each site is indexed with `terrain_type`, coordinates, measured
profile and a discovery note. Cave sites are surface-profiled with
documented cave metadata — disclosed, not disguised. → `04`

### Objective 3 — Actionable Output Delivery
*Benchmark: functional web interfaces displaying similarity rankings,
geographic coordinates and metadata overlays.*
**Met.** Six-page Streamlit app: ranked tables per base, a Folium world
map with per-site metadata popups, head-to-head comparisons, radar plots,
and CSV downloads of every output. → `07`

### Objective 4 — Multi-Variable Similarity Scoring
*Benchmark: match metrics factoring thermal inertia, mineralogical
composition and aridity indices; weighting and clustering algorithms.*
**Met, with one honest substitution.** Weighted Euclidean dissimilarity
over slope / flat-area / temperature / relief / regolith-proxy pillars,
plus K-Means regime clustering. The soil pillar (sand/clay/coarse
fragments) is the mineralogical-composition input available globally at
site scale. Direct *thermal inertia* and *aridity index* layers are not
separately integrated: temperature and seasonal range carry the thermal
behaviour, and the soil + temperature combination carries aridity — stated
here and in the methodology rather than relabelled. → `06`

### Objective 5 — Environmental Stress Simulation
*Benchmark: factor seasonal fluctuations (monsoons, freeze–thaw) into the
matching.*
**Met at the data level.** Every Earth profile includes the seasonal
temperature range (warmest − coldest month, NASA POWER); every Moon
profile is built from two Diviner seasonal slices (winter + opposite
season), so both sides of the comparison carry seasonal behaviour into the
published profiles (e.g. Elgygytgyn's 38.4 °C annual swing — the pool's
largest — is part of why it profiles as a polar-analog regime member).
Seasonal range is displayed in the ranking table; it is not a separate
scoring pillar in v1 — disclosed here. → `03`, `04`

### Objective 6 — Mission-Specific Customization
*Benchmark: customizable filters / dynamic re-weighting depending on
whether the mission prioritizes rover mobility, life-support, or
structural habitat testing.*
**Met — implemented as live controls.** The Finder page offers Rover
mobility, Habitat & structures and Science & ISRU presets plus free
sliders for all five weights, recomputing rankings in-page from the stored
per-pillar distances, with the official default ranking one click away.
The interaction is covered by automated AppTest. → `07`

## Part B — The seven questions (Section 7 of the guide)

1. **Solar illumination angles / perpetual darkness when matching caves
   and polar canyons?** ATLAS uses PGDA-69's modelled 18.6-year average
   solar and Earth visibility per base plus LPSR shadow masks rather than
   re-deriving illumination geometry. For Earth cave analogs, darkness is
   intrinsic to the documented cave systems; their surface boxes profile
   the host volcanic terrain. Rim-vs-floor lighting contrast (the guide's
   Shackleton diagram) is exactly what the PSR % and sun % columns
   quantify per base.
2. **Spectroscopic / neutron layers for volatile traps?** Volatile context
   in v1 = LPSR permanently-shadowed fraction + Diviner cold-trap
   temperatures (1st-percentile 34–39 K). Dedicated LEND neutron and M³
   spectrometer layers are **roadmap, not integrated** — stated openly.
3. **Normalising coarse planetary telemetry against fine terrestrial
   rasters?** Comparisons use ROI/box *statistics* (means, percentiles,
   fractions), never pixel-to-pixel matching across the 240 m / 30 m gap;
   every variable is min–max normalised over the combined Moon+Earth set.
   The residual resolution effect is Limitation 2 (conservative
   direction).
4. **Distance metrics / ML clustering?** Weighted Euclidean dissimilarity
   (published weights) **and** K-Means (k=3) regime clustering with
   mechanically-derived labels. Cosine similarity was considered and not
   used: it ignores magnitude, and magnitude (how steep, how cold) is the
   signal here.
5. **DEMs / LiDAR for underground analogs?** Cave systems are documented
   from the geological literature (Undara ~160 km of tubes; Manjanggul
   7.4 km, multi-level) and profiled via their surface DEM boxes. LiDAR
   cave surveys (e.g. USGS 3DEP-class data) are roadmap; no underground
   raster is claimed in v1.
6. **Dynamic re-weighting by hardware being tested?** Yes — presets and
   sliders (Objective 6 above), including an abrasiveness-leaning profile
   via the Science & ISRU preset's soil weight. A dedicated UV-index
   pillar is not in v1.
7. **Validation against historical field data?** Two independent checks:
   (a) the control run — the untuned engine ranks the literature's
   canonical analogs (McMurdo, Atacama) #1 when they are in the pool;
   (b) profile verification — every base profile was checked against
   published site character and named-crater geometry before scoring.
   → `08`

## Part C — What ATLAS deliberately does *not* claim

- No global scan (14 curated novel sites, not a planetary search) — the
  team's ETOPO/MODIS design is the documented next step.
- No neutron/spectrometer volatile layers, no LiDAR cave geometry, no UV
  pillar, no thermal-inertia layer (see Objective 4 note).
- No Mars ranking — one measured Mars region (Jezero) as a method
  demonstration.
- Scores are *within-pool rankings*: adding sites renormalises the scale.
  This is stated wherever scores are shown.

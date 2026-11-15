# ATLAS — Dataset Documentation & Data Architecture

**Project:** ATLAS (*Analog Terrain & Lunar Alignment System*)  
**Team:** Binary Knights  
**Challenge:** NASA Space Apps Challenge 2026  
**Target Environment:** Python 3, GDAL / Rasterio, Scikit-learn, Streamlit (< 8 GB RAM constraint)

---

## 1. Overview & Data Strategy

ATLAS identifies terrestrial analog sites on Earth that closely match the geophysical conditions of candidate lunar base locations—specifically the **Lunar South Pole ($-80^\circ$ to $-90^\circ$ latitude)**. Rather than relying on single-variable heuristics, the pipeline evaluates candidate locations across three core planetary pillars:

1. **Terrain & Topography:** Elevation relief, slope steepness, surface roughness, and solar illumination / shadow persistence.
2. **Thermal Regime:** Seasonal temperature extremes, mean surface/soil temperatures, and diurnal thermal swings.
3. **Surface Geology & Composition:** Rock/boulder abundance, regolith exposure, and thermal infrared emissivity.

All datasets are staged under `ATLAS/data/` in compressed or raster-ready formats (`GeoTIFF`, `JPEG2000`, `PDS IMG/LBL`, `PDS TAB`, and `HDF4`) totaling **$\approx 3.16\text{ GB}$** on disk, designed to be processed in `float32` precision within an **8 GB RAM** budget.

---

## 2. Directory Structure

```text
ATLAS/
├── DATA_DOCUMENTATION.md
├── src/
└── data/
    ├── moon/
    │   ├── terrain.htm                                   (14.8 KB)
    │   ├── temperature.htm                               (14.0 KB)
    │   ├── terrain/
    │   │   ├── ldem_80s_80m.img                          (115.5 MB)
    │   │   ├── ldem_80s_80m.lbl                          (5.0 KB)
    │   │   ├── ldrm_75s_240m.img                         (29.1 MB)
    │   │   ├── ldrm_75s_240m.lbl                         (4.1 KB)
    │   │   ├── ldsm_75s_240m.img                         (29.1 MB)
    │   │   ├── ldsm_75s_240m.lbl                         (4.0 KB)
    │   │   ├── lpsr_81s_240m.jp2                         (901.4 KB)
    │   │   ├── lpsr_81s_240m_jp2.lbl                     (4.9 KB)
    │   │   └── lpsr_81s_240m_jp2_aux.xml                 (1.3 KB)
    │   └── temperature/
    │       ├── dgdr_ra_avg_cyl_128_jp2.jp2               (198.8 MB)
    │       ├── dgdr_ra_avg_cyl_128_jp2.lbl               (5.2 KB)
    │       ├── dgdr_st_avg_cyl_128_jp2.jp2               (630.8 MB)
    │       ├── dgdr_st_avg_cyl_128_jp2.lbl               (5.2 KB)
    │       ├── pcp_avg_tbol_pols_win_slon01_240.tab      (181.2 MB)
    │       ├── pcp_avg_tbol_pols_win_slon01_240.lbl      (3.6 KB)
    │       ├── pcp_avg_tbol_pols_win_slon48_240.tab      (176.7 MB)
    │       └── pcp_avg_tbol_pols_win_slon48_240.lbl      (3.6 KB)
    └── earth/
        ├── terrain/
        │   └── ETOPO_2022_v1_60s_N90W180_surface.tif     (466.0 MB)
        ├── temperature/
        │   ├── MOD11C3.A2025182.061.2025213154157.hdf    (71.4 MB)
        │   └── MOD11C3.A2026001.061.2026034041909.hdf    (71.7 MB)
        └── landcover/
            └── MCD12C1.A2025001.061.2026269181218.hdf    (1.24 GB)
```

---

## 3. Lunar Baseline Datasets (`data/moon/`)

> **Repository note:** no data files, labels or manifests are stored in this GitHub repository. The `data/moon/` paths in this section describe the **local** data tree created by `scripts/download_data.sh` (git-ignored); every `.lbl` label travels with its PDS product download. An earlier commit carried a partial set of downloaded labels and saved ODE web pages — removed as clutter (south-pole only, and two labels described the unused cylindrical products in §3.2).

All lunar datasets originate from NASA's **Lunar Reconnaissance Orbiter (LRO)** and were queried via the **NASA PDS Geosciences Node — Lunar Orbital Data Explorer (ODE)**. Every raster or table is accompanied by its detached PDS3 label file (`.lbl`), which provides map projection parameters, scale factors, and nodata values required by `GDAL` / `rasterio`.

### 3.1 Lunar Terrain & Illumination (`data/moon/terrain/`)
* **Instrument:** LOLA (*Lunar Orbiter Laser Altimeter*)
* **Projection:** South Polar Stereographic

| Filename | Product Type | Spatial Coverage & Resolution | Size | Role in ATLAS Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| `ldem_80s_80m.img` (+ `.lbl`) | PDS4 Gridded Data Record Shape Map (`GDRDEM`) | $-80^\circ$ to $-90^\circ$ S, $80\text{ m/px}$ | $115.5\text{ MB}$ | High-precision elevation model used to establish Lunar South Pole crater relief and elevation variance baselines. |
| `ldrm_75s_240m.img` (+ `.lbl`) | PDS4 Gridded Data Record Roughness Map (`GDRDRM`) | $-75^\circ$ to $-90^\circ$ S, $240\text{ m/px}$ | $29.1\text{ MB}$ | Quantifies surface topographic roughness at rover/lander scales to constrain mobility and landing safety. |
| `ldsm_75s_240m.img` (+ `.lbl`) | PDS4 Gridded Data Record Slope Map (`GDRDSM`) | $-75^\circ$ to $-90^\circ$ S, $240\text{ m/px}$ | $29.1\text{ MB}$ | Pre-computed surface slope gradients (in degrees) defining safe operational terrain thresholds. |
| `lpsr_81s_240m.jp2` (+ `.lbl`, `.xml`) | PDS3 Permanently Shadowed Regions (`GDRPSR`) | $-81^\circ$ to $-90^\circ$ S, $240\text{ m/px}$ | $901.4\text{ KB}$ | Binary/fractional mask of Permanently Shadowed Regions (PSRs) indicating volatile cold traps and extreme illumination constraints. |

### 3.2 Lunar Temperature & Surface Geology (`data/moon/temperature/`)
* **Instrument:** DLRE (*Diviner Lunar Radiometer Experiment*)

| Filename | Product Type | Spatial Coverage & Resolution | Size | Role in ATLAS Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| `pcp_avg_tbol_pols_win_slon01_240.tab` (+ `.lbl`) | PDS4 Polar Cumulative Product (`PCP`) — Bolometric Temp | $-80^\circ$ to $-90^\circ$ S, $240\text{ m/px}$ | $181.2\text{ MB}$ | South Pole average bolometric surface temperature ($\text{K}$) during Solar Longitude Slice 01 (peak lunar polar winter / cold extreme). |
| `pcp_avg_tbol_pols_win_slon48_240.tab` (+ `.lbl`) | PDS4 Polar Cumulative Product (`PCP`) — Bolometric Temp | $-80^\circ$ to $-90^\circ$ S, $240\text{ m/px}$ | $176.7\text{ MB}$ | South Pole average bolometric surface temperature ($\text{K}$) during Solar Longitude Slice 48 (opposite seasonal extreme). |
| `dgdr_st_avg_cyl_128_jp2.jp2` (+ `.lbl`) | PDS4 Gridded Data Record Level 3 (`GDR_L3`) — Soil Temp | $-60^\circ$ to $+60^\circ$, $128\text{ px/deg}$ | $630.8\text{ MB}$ | Multi-year diurnal average regolith temperature ($\text{K}$) providing a global lunar thermal reference distribution. |
| `dgdr_ra_avg_cyl_128_jp2.jp2` (+ `.lbl`) | PDS4 Gridded Data Record Level 3 (`GDR_L3`) — Rock Abundance | $-60^\circ$ to $+60^\circ$, $128\text{ px/deg}$ | $198.8\text{ MB}$ | Multi-year average areal fraction of exposed rocks/boulders versus fine regolith (geological hazard and surface composition feature). |

### 3.3 Archive Manifests
* The Lunar ODE cart manifests (`terrain.htm`, `temperature.htm`) record the exact PDS archive URLs and product IDs used. They are working files from the data-collection step and are **not** kept in the repository — the same product URLs are encoded in `scripts/download_data.sh`, which is the reproducibility record.

---

## 4. Terrestrial Candidate Datasets (`data/earth/`)

All terrestrial datasets cover the full globe ($-90^\circ$ to $+90^\circ$ latitude, $-180^\circ$ to $+180^\circ$ longitude) so that high-latitude polar deserts—such as the **Antarctic Dry Valleys**, **Devon Island**, and **Svalbard**—are evaluated alongside mid-latitude arid basins like the **Atacama Desert** and **Mojave Desert**.

### 4.1 Earth Terrain & Elevation (`data/earth/terrain/`)
* **Source:** NOAA National Centers for Environmental Information (NCEI)

| Filename | Dataset | Spatial Resolution & Grid | Size | Role in ATLAS Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| `ETOPO_2022_v1_60s_N90W180_surface.tif` | ETOPO 2022 Global Relief Model (Ice Surface Elevation) | $60\text{ arc-seconds}$ ($\approx 1.85\text{ km}$), Global GeoTIFF | $466.0\text{ MB}$ | Provides continuous global land and ice-sheet elevation ($\text{m}$). Resampled to $0.05^\circ$ to derive terrestrial elevation, slope, and local terrain roughness. |

### 4.2 Earth Temperature & Thermal Emissivity (`data/earth/temperature/`)
* **Source:** NASA Earthdata Search / LP DAAC (`MOD11C3` Version 061)
* **Sensor:** MODIS (*Moderate Resolution Imaging Spectroradiometer*) on NASA Terra

| Filename | Acquisition Window | Spatial Resolution & Grid | Size | Role in ATLAS Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| `MOD11C3.A2025182.061.2025213154157.hdf` | July 2025 (`2025-07-01` to `2025-07-31`) | $0.05^\circ$ CMG ($3600 \times 7200$) | $71.4\text{ MB}$ | Captures Northern Hemisphere summer and Antarctic peak winter Daytime/Nighttime Land Surface Temperature ($\text{LST}$) plus thermal emissivity. |
| `MOD11C3.A2026001.061.2026034041909.hdf` | January 2026 (`2026-01-01` to `2026-01-31`) | $0.05^\circ$ CMG ($3600 \times 7200$) | $71.7\text{ MB}$ | Captures Northern Hemisphere winter and Antarctic peak summer $\text{LST}$, enabling calculation of annual mean temperature, seasonal amplitude, and diurnal swing ($\Delta T$). |

> **Geological Proxy Note:** In addition to `LST_Day_CMG` and `LST_Night_CMG`, `MOD11C3` provides thermal infrared emissivity bands (`Emis_29`, `Emis_31`, `Emis_32` spanning $8.5\text{--}12.0\ \mu\text{m}$). These Reststrahlen-band emissivities serve as a direct silicate/mineralogical analog to LRO Diviner's thermal infrared channels.

### 4.3 Earth Land Cover & Environmental Mask (`data/earth/landcover/`)
* **Source:** NASA Earthdata Search / LP DAAC (`MCD12C1` Version 061)
* **Sensor:** MODIS Terra + Aqua Combined

| Filename | Acquisition Window | Spatial Resolution & Grid | Size | Role in ATLAS Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| `MCD12C1.A2025001.061.2026269181218.hdf` | Full Year 2025 | $0.05^\circ$ CMG ($3600 \times 7200$) | $1.24\text{ GB}$ | Aligns pixel-for-pixel with `MOD11C3` to mask out oceans, dense vegetation, croplands, and urban zones, isolating **IGBP Class 16 (Barren / Sparsely Vegetated)** and **IGBP Class 15 (Permanent Snow & Ice)**. |

---

## 5. Cross-Planetary Feature Alignment Matrix

During preprocessing (`src/preprocess.py`), Earth rasters are standardized onto the **$0.05^\circ$ Climate Modeling Grid ($3600 \times 7200$ pixels, $\approx 5.6\text{ km}$ at the equator)** and compared against statistical feature vectors extracted from the Lunar South Pole baseline:

| Geophysical Pillar | Lunar Baseline Feature (LRO) | Terrestrial Analog Feature (Earth) | Alignment / Transformation Method |
| :--- | :--- | :--- | :--- |
| **Elevation & Relief** | `ldem_80s_80m` local relief & std. dev. | `ETOPO_2022` elevation & local relief | Area-weighted resampling from $60\text{ arc-sec}$ to $0.05^\circ$ grid. |
| **Slope Gradient** | `ldsm_75s_240m` mean/percentile slope | Horn's gradient algorithm on `ETOPO_2022` | Computed in degrees ($\arctan(\sqrt{(dz/dx)^2 + (dz/dy)^2})$) before aggregation. |
| **Surface Roughness** | `ldrm_75s_240m` roughness index | Terrain Ruggedness Index (TRI) from `ETOPO_2022` | Standard deviation of elevation within moving $3 \times 3$ kernel. |
| **Mean & Extreme Temp** | `pcp_avg_tbol_pols` (`slon01`, `slon48`) & `dgdr_st_avg` | `MOD11C3` July/Jan `LST_Day` & `LST_Night` | Scaled by $0.02\text{ K}$ factor; seasonal min, max, mean, and diurnal $\Delta T$ derived. |
| **Surface Composition** | `dgdr_ra_avg` rock abundance & PSR fraction | `MOD11C3` `Emis_29/31/32` & `MCD12C1` Class 15/16 | Non-barren/non-ice pixels masked (`NaN`); standardized via `StandardScaler`. |
---

# Version 2 — As Built (14 Nov 2026)

The pipeline described above was reviewed against the challenge (see the
team review notes) and then **built**. Three coverage problems in the v1
plan were fixed, and the Earth side was changed to a fine-resolution
two-stage design. This section is the documentation of what ATLAS
actually uses now. The v1 text above is kept for history.

## Corrections to v1

1. **North Pole added.** v1 covered only the Lunar South Pole, so **Peary
   (88.63°N, 24.4°E) had no data at all**. Added: LDEM_80N_80M,
   LDSM_75N_240M, LDRM_75N_240M (PDS), LPSR_81N_240M, PGDA-69 north
   illumination set (85N, 60 m), and Diviner PCP **poln** tables.
2. **Diviner cylindrical files removed from the baseline.**
   `dgdr_st_avg_cyl_128` (soil temperature) and `dgdr_ra_avg_cyl_128`
   (rock abundance) cover only **−60°…+60° latitude**; none of the four
   polar bases exists in them (~830 MB unusable at the bases). Temperature
   comes from the PCP polar tables (pols **and** poln, slon01 + slon48),
   which were already in v1 and are correct.
3. **Illumination added.** v1 had PSR only. Added PGDA Product 69
   AVGVISIB maps: average **solar** visibility and average **Earth**
   visibility — 85S 60 m (Shackleton, de Gerlache), 75S 120 m (Amundsen),
   85N 60 m (Peary).
4. **Earth terrain resolution fixed.** v1 resampled ETOPO to a 0.05°
   (≈5.6 km) grid; at that size Meteor Crater (~1.2 km) is smaller than
   one pixel and slopes are not comparable to the Moon's 240 m product.
   ATLAS as built profiles eight candidate sites in fixed 20 × 20 km
   boxes from **Copernicus DEM GLO-30 (30 m)**, with **NASA POWER**
   temperature climatology and **SoilGrids 2.0** soil (sand/clay/coarse
   fragments) — the soil dataset v1 lacked. The ETOPO/MODIS global scan
   remains a documented next step, not the scoring input.
5. **Per-base profiles, not one pooled vector.** Each base gets its own
   ROI (Shackleton 15 km, de Gerlache 20 km, Peary 40 km, Amundsen 60 km
   radius) and its own ranking of Earth sites. Base centres are the IAU
   centres — note Shackleton's centre is **89.67°S, 129.78°E** (the pole
   sits on its rim); the often-quoted "89.9°S, 0°E" is not the centre and
   visibly mis-centres the crater.

## Processing warnings discovered while building (read before reusing code)

- **LDSM DN = 0 is no-data**, not 45°. It spikes at ~29% of the polar cap;
  DN-0 pixels have ordinary ~10° DEM-gradient slopes. `preprocess_moon.py`
  excludes DN 0 from every slope statistic.
- **North-pole GDR grids have the opposite row handedness** to south-pole
  grids. Validated by crater-depression tests (Rozhdestvenskiy, Byrd,
  Sylvester, Peary in the north; Amundsen, Shoemaker, Faustini, Haworth,
  Sverdrup in the south). `atlas_common.latlon_to_pixel` handles both.
- **Diviner PCP raw bin minima can be outliers** (a single 12 K bin in the
  Amundsen ROI). Cold extremes are reported as the 1st percentile.

## Mars

USGS's mosaic server blocks scripted range access (HTTP 403), so the Mars
quick-look reads the **PDS MOLA MEGDR** tile `megt44n000hb` by HTTP range
requests — only the ~3 MB Jezero Crater window is fetched from the 130 MB
tile. Output: `outputs/mars_profiles.csv`.

---

# Version 3 — Novel-Site Discovery Run (Challenge Guide #09)

The local event's Challenge Guide #09 makes **novelty** the core task: its
Introduction and Background direct participants to discover uncatalogued
analogs and name the world-renowned sites (Atacama, Mauna Loa, Haughton…)
as the already-done set. ATLAS was therefore re-run as a discovery engine:

- **Excluded by design:** Atacama, Mauna Loa / Mauna Kea, Haughton Crater,
  Rio Tinto, Iceland, Mojave, McMurdo Dry Valleys, Meteor Crater, Svalbard,
  Wadi Rum, Pilbara. (They served as the validation control: with them
  included, the engine ranked McMurdo #1 for 3 of 4 bases and Atacama #1
  for Peary — the literature's answers, untuned.)
- **Discovery pool (14 sites, 6 terrain types):** Lut Desert and Qaidam
  Basin and Badain Jaran (arid basins); Etosha Pan and Salinas Grandes
  (salt flats); Mount Erebus, Deception Island and Kamchatka (volcanic
  fields); Undara and Manjanggul lava tubes (subterranean caves); Yamal
  Peninsula (permafrost); Elgygytgyn, Lonar and Tenoumer (lesser-known
  impact structures). Each site record carries a `terrain_type` and an
  `analog_note` explaining why it is a new candidate.
- **Guide Objective 6 implemented:** the app's Finder page re-weights the
  score live (Rover mobility / Habitat & structures / Science & ISRU
  presets + sliders), recomputing from stored per-factor distances.
- **Guide Objective 4 extended:** K-Means clustering (k=3) groups the
  sites into environmental regimes (`regime` column).
- Island/coastal sites (Erebus, Deception Island, Jeju) mask sea pixels
  (DEM elevation ≤ 0.5 m) so ocean does not dilute their terrain stats.

---

# Direct Data Links — As Built (added 15 Nov 2026)

These are the exact sources the **final** ATLAS pipeline used — the same lists
submitted in the NASA Data and Space Agency Partner & Other Data sections of
the Space Apps global portal. All links verified live on 15 November 2026.
Exact file-level URLs for every download are encoded in
`scripts/download_data.sh`, which remains the reproducibility record.

## NASA data

| Dataset | Used for | Direct link |
| :--- | :--- | :--- |
| LRO LOLA Gridded Data Records (LDEM / LDSM / LDRM) | Moon polar elevation, slope and roughness for all 4 bases, both poles | https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx |
| LRO LOLA Permanently Shadowed Region Maps (LPSR) | PSR % per base study area | https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx |
| LRO Diviner Polar Cumulative Products (PCP) | Bolometric surface temperature, both poles (pols + poln, winter + opposite-season slices) | https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/diurnal/ |
| Lunar Illumination & Average Visibility Maps (Mazarico et al. 2011; PGDA 69) | Sun visibility % and Earth visibility % per base | http://imbrium.mit.edu/EXTRAS/ILLUMINATION/IMG/ |
| NASA PGDA — LOLA Polar Products Catalog | Product identification for the polar DEMs (South Pole mosaic, 80S mosaic, North Pole grids) | https://pgda.gsfc.nasa.gov/ |
| MGS MOLA MEGDR | Mars topography — Jezero Crater profile | https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/ |
| NASA POWER Climatology | Earth-site mean and seasonal temperatures (API: https://power.larc.nasa.gov/api/temporal/climatology/point) | https://power.larc.nasa.gov/ |

## Space Agency Partner & other data

| Dataset / resource | Used for | Direct link |
| :--- | :--- | :--- |
| Copernicus DEM GLO-30 (ESA / Airbus) | Earth elevation and slope at native 30 m for all 14 candidate sites | https://copernicus-dem-30m.s3.amazonaws.com/ |
| SoilGrids 2.0 (ISRIC) | Soil pillar — sand, clay and coarse-fragment fractions (0–5 cm) | https://soilgrids.org |
| Google Maps embedded tiles | Basemap imagery in the web app (free tile service, no API key) | https://www.google.com/maps |
| Leaflet (open-source library) | Interactive map in the web app | https://leafletjs.com |

## Documented in v1 but NOT used in the final pipeline

For the record: the v1 plan in this document also listed ETOPO 2022,
MODIS MOD11C3 / MCD12C1, and Diviner cylindrical soil-temperature and
rock-abundance products. These were **not** used in the final build — ETOPO
was replaced by Copernicus GLO-30 (finer resolution), MODIS temperatures by
NASA POWER climatology, and the cylindrical Diviner products (which cover
only −60°…+60° latitude) by the polar PCP tables. They are therefore not
listed in the portal submission either.

# ATLAS: Analog Terrain & Lunar Alignment System

**Team:** Binary Knights  
**Event:** NASA Space Apps Challenge 2026  
**Domain:** Planetary Science, Geospatial Machine Learning & Mission Readiness  

> **ATLAS** is an end-to-end geospatial machine learning pipeline and interactive decision-support tool that identifies and ranks terrestrial analog sites on Earth matching the geophysical, thermal, and geological conditions of candidate Lunar South Pole ($-80^\circ$ to $-90^\circ$) landing zones.

---

## 1. Mission Context & Problem Statement

Before deploying astronauts, pressurized rovers, or In-Situ Resource Utilization (ISRU) hardware to the **Lunar South Pole** under NASA's Artemis program, mission planners must validate equipment in **terrestrial analog environments** on Earth. Historically, analog selection has relied on manual, single-variable heuristics—such as picking a site solely because it is cold or rocky—overlooking critical multi-factor interactions between **topographic slope**, **diurnal/seasonal thermal swings**, and **surface regolith/rock composition**.

**ATLAS** solves this by framing analog discovery as a multi-modal cross-planetary similarity problem:
1. **Quantifies the Lunar Baseline:** Extracts high-resolution topographic, illumination, thermal, and rock-abundance distributions directly from NASA Lunar Reconnaissance Orbiter (**LRO**) datasets.
2. **Masks Non-Analog Earth Environments:** Automatically filters out oceans, forests, croplands, and urban areas using global satellite land-cover classification, isolating barren regolith and polar ice sheets.
3. **Scores & Ranks Earth Analogs:** Aligns global Earth datasets onto a unified spatial grid and applies standardized, weighted multi-criteria machine learning to score every valid terrestrial cell against lunar mission profiles.

---

## 2. System Architecture

```text
+-----------------------------------+      +-----------------------------------+
|      LUNAR BASELINE (LRO)         |      |    TERRESTRIAL CANDIDATES (EARTH) |
|  - LOLA DEM, Slope, Roughness     |      |  - NOAA ETOPO 2022 Elevation      |
|  - LOLA PSR Illumination Mask     |      |  - MODIS MOD11C3 LST & Emissivity |
|  - Diviner Bolometric & Soil Temp |      |  - MODIS MCD12C1 Land Cover Mask  |
|  - Diviner Rock Abundance         |      |                                   |
+-----------------+-----------------+      +-----------------+-----------------+
                  |                                          |
                  v                                          v
+-----------------------------------+      +-----------------------------------+
|   Lunar Target Profile Extractor  |      |   Earth Spatial Grid Aligner      |
|  - South Pole (-80 to -90 deg)    |      |  - 0.05 deg CMG (3600 x 7200)     |
|  - Crater Rim vs. Cold Trap Stats |      |  - Horn Slope & TRI Roughness     |
|  - Target Feature Vector (mu, IQR)|      |  - IGBP Class 15 & 16 Masking     |
+-----------------+-----------------+      +-----------------+-----------------+
                  |                                          |
                  +--------------------+---------------------+
                                       |
                                       v
                  +-----------------------------------------+
                  |      ML ANALOG ENGINE (src/model.py)    |
                  |  - Robust/Standard Feature Scaling      |
                  |  - Weighted Multi-Pillar Similarity     |
                  |  - K-Means Geophysical Regime Clustering|
                  +--------------------+--------------------+
                                       |
                                       v
                  +-----------------------------------------+
                  |   INTERACTIVE DASHBOARD (src/app.py)    |
                  |  - Streamlit + Folium Global Map        |
                  |  - Dynamic Pillar Weight Sliders        |
                  |  - Radar Profiles & CSV/GeoJSON Export  |
                  +-----------------------------------------+
```

For full specifications, file sizes, projections, and scientific roles of all staged files, see [`DATA_DOCUMENTATION.md`](./DATA_DOCUMENTATION.md).

---

## 3. Repository & Data Structure

```text
ATLAS/
├── README.md                                             # Project architecture, implementation & execution plan
├── DATA_DOCUMENTATION.md                                 # Comprehensive catalog of staged Moon & Earth datasets
├── environment.yml                                       # Reproducible Conda environment specification
├── src/
│   ├── preprocess.py                                     # Phase 2: Raster alignment, feature extraction & Parquet export
│   ├── model.py                                          # Phase 3: Feature scaling, analog scoring & clustering
│   └── app.py                                            # Phase 4: Streamlit + Folium interactive analog explorer
├── outputs/
│   ├── lunar_baselines.json                              # Extracted Lunar South Pole target signatures
│   ├── earth_features.parquet                            # Memory-optimized aligned Earth feature matrix
│   └── analog_ranked_sites.parquet                       # Scored & clustered terrestrial analog candidates
└── data/                                                 # ~3.16 GB raw NASA/NOAA datasets (git-ignored)
    ├── moon/
    │   ├── terrain/                                      # LRO LOLA DEM, Roughness, Slope, PSR (.img/.jp2 + .lbl)
    │   └── temperature/                                  # LRO Diviner Polar & Cylindrical Temp/Rock (.tab/.jp2 + .lbl)
    └── earth/
        ├── terrain/                                      # ETOPO_2022_v1_60s_N90W180_surface.tif
        ├── temperature/                                  # MOD11C3 July 2025 & January 2026 (.hdf)
        └── landcover/                                    # MCD12C1 2025 Global Land Cover (.hdf)
```

---

## 4. Detailed Implementation Plan

The codebase is engineered around a strict **$< 8\text{ GB}$ RAM constraint** on Windows. Every spatial array is cast to `float32`, processed band-by-band with explicit garbage collection (`del`, `gc.collect()`), and serialized into columnar **Apache Parquet** format so the ML engine and web UI never touch multi-gigabyte raw rasters at runtime.

### Module 1: Lunar Baseline Extraction (`src/preprocess.py` — Part A)
* **Inputs:** `ldem_80s_80m.lbl`, `ldsm_75s_240m.lbl`, `ldrm_75s_240m.lbl`, `lpsr_81s_240m_jp2.lbl`, `pcp_avg_tbol_pols_win_slon01_240.tab`, `pcp_avg_tbol_pols_win_slon48_240.tab`, and `dgdr_ra_avg_cyl_128_jp2.lbl`.
* **Processing Logic:**
  1. Read LOLA South Polar Stereographic rasters via `rasterio` using their detached PDS3 `.lbl` metadata headers.
  2. Parse Diviner South Pole `.tab` cumulative tables (`slon01` winter cold extreme and `slon48` opposite seasonal extreme) to compute bolometric temperature distributions.
  3. Extract summary geophysical vectors (median, interquartile range, 10th percentile, 90th percentile) across three distinct **Lunar Mission Archetypes**:
     * **Archetype A — Illuminated Crater Rim (e.g., Shackleton Rim):** Low slope ($< 10^\circ$), low roughness, high solar visibility, moderate polar thermal stability.
     * **Archetype B — Permanently Shadowed Cold Trap (PSR Interior):** High PSR fraction ($> 0.8$), cryogenic temperatures ($< 110\text{ K}$), high volatile-retention potential.
     * **Archetype C — Rough Regolith / Boulder Field:** Elevated roughness and rock abundance fraction for rover hazard-avoidance testing.
* **Output:** `outputs/lunar_baselines.json`.

### Module 2: Earth Grid Alignment & Feature Engineering (`src/preprocess.py` — Part B)
* **Target Spatial Grid:** $0.05^\circ$ Climate Modeling Grid ($3600 \times 7200 = 25,920,000$ global cells; $\approx 5.6\text{ km}$ resolution at the equator; $\approx 98.8\text{ MB}$ per `float32` layer).
* **Processing Logic:**
  1. **Land Cover Filtering (`MCD12C1`):** Extract `Majority_Land_Cover_Type_1` (IGBP classification). Retain only **Class 15 (Permanent Snow & Ice)** and **Class 16 (Barren or Sparsely Vegetated)**. Mask all oceans (Class 0) and vegetated/urban classes (Classes 1–14) to reduce active candidate pixels by $\approx 82\%$ ($\sim 4.5\text{ million}$ valid land cells).
  2. **Terrain Derivation (`ETOPO_2022`):** Compute pixel-wise slope in degrees using Horn's $3 \times 3$ gradient method:
     $$\theta = \arctan\left(\sqrt{\left(\frac{dz}{dx}\right)^2 + \left(\frac{dz}{dy}\right)^2}\right) \times \frac{180}{\pi}$$
     Compute local Terrain Ruggedness Index ($\text{TRI}$) as the $3 \times 3$ moving standard deviation of elevation, then area-average elevation, slope, and $\text{TRI}$ from $60\text{ arc-seconds}$ onto the $0.05^\circ$ grid.
  3. **Thermal & Emissivity Extraction (`MOD11C3`):** Load July 2025 (`A2025182`) and January 2026 (`A2026001`) `LST_Day_CMG` and `LST_Night_CMG` subdatasets, apply the MODIS scale factor ($0.02\text{ K}$), and derive:
     * Annual mean surface temperature ($T_{\text{mean}}$)
     * Extreme cold minimum ($T_{\min}$) and extreme warm maximum ($T_{\max}$)
     * Mean diurnal temperature swing ($\Delta T_{\text{diurnal}} = T_{\text{day}} - T_{\text{night}}$)
     * Thermal infrared mineralogical emissivity (`Emis_29`, `Emis_31`, `Emis_32` scaled by $0.002 + 0.49$).
* **Output:** `outputs/earth_features.parquet` ($\approx 120\text{ MB}$ compressed).

### Module 3: Multi-Criteria Similarity & Clustering Engine (`src/model.py`)
* **Feature Normalization:** Apply `RobustScaler` (median and IQR scaling) across terrestrial candidate features so extreme Himalayan elevations or Antarctic cold anomalies do not distort distance metrics.
* **Domain-Bridged Similarity Scoring:** Because Earth's absolute atmospheric temperature ($\sim 210\text{--}310\text{ K}$) differs from airless lunar radiative temperatures ($\sim 40\text{--}220\text{ K}$), ATLAS uses a hybrid scoring function combining **normalized structural similarity** (relative thermal swing, slope, roughness, emissivity) and **regime alignment**:
  $$D_{\text{weighted}}(x_i, \mu_L) = \sqrt{w_{\text{terrain}} \, d_{\text{terrain}}^2 + w_{\text{thermal}} \, d_{\text{thermal}}^2 + w_{\text{geology}} \, d_{\text{geology}}^2}$$
  $$\text{Analog Score}(x_i) = 100 \times \exp\left(-\alpha \, D_{\text{weighted}}(x_i, \mu_L)\right) \in [0, 100]$$
  where $w_{\text{terrain}} + w_{\text{thermal}} + w_{\text{geology}} = 1$ are user-adjustable pillar weights.
* **Unsupervised Regime Clustering:** Fit `MiniBatchKMeans` ($K = 8$) on the valid barren/ice feature matrix to automatically segment Earth's surface into distinct geophysical analog zones (e.g., *Polar Hyper-Arid Ice Sheets*, *Cold High-Altitude Volcanic Plateaus*, *Hyper-Arid Mid-Latitude Basins*, *Steep Crater-Like Massifs*).
* **Output:** `outputs/analog_ranked_sites.parquet` and serialized scaler/cluster artifacts.

### Module 4: Interactive Mission Planner Dashboard (`src/app.py`)
* **Framework:** Streamlit + Folium (`streamlit-folium`) + Plotly.
* **Core Capabilities:**
  * **Mission Preset Selector:** Switch between *Artemis Crater Rim*, *PSR Cold Trap*, and *Rover Mobility Testbed*.
  * **Live Weight Tuning:** Interactive sliders for **Terrain Weight**, **Thermal Weight**, and **Geology Weight** that recompute Analog Scores in $< 0.3\text{ seconds}$ using vectorized NumPy operations.
  * **Interactive Global Map:** Folium heatmap and top-$N$ ranked site markers with latitude/longitude, elevation, slope, temperature swing, and dominant analog cluster popups.
  * **Comparative Telemetry View:** Side-by-side radar chart and distribution comparison between any clicked Earth site and the Lunar South Pole baseline, plus one-click CSV/GeoJSON export.

---

## 5. Phase-by-Phase Execution Plan

### Phase 1: Environment Setup & Subdataset Inspection
Verify that Conda installs GDAL with **HDF4** drivers enabled and inspect the exact internal subdataset names of your staged `.hdf`, `.lbl`, and `.tab` files.

```powershell
# 1. Install geospatial, ML, and visualization dependencies in Conda (base)
conda install -y -c conda-forge rasterio gdal scikit-learn pandas pyarrow streamlit folium streamlit-folium plotly

# 2. Verify HDF4, PDS3 label, and Diviner TAB readability
python -c "
import rasterio
with rasterio.open('data/earth/temperature/MOD11C3.A2026001.061.2026034041909.hdf') as s:
    print('MOD11C3:', s.subdatasets[:6])
with rasterio.open('data/earth/landcover/MCD12C1.A2025001.061.2026269181218.hdf') as s:
    print('MCD12C1:', s.subdatasets[:2])
with rasterio.open('data/moon/terrain/ldem_80s_80m.lbl') as s:
    print('LOLA DEM:', s.shape, s.crs)
"
```

### Phase 2: Preprocessing & Feature Matrix Generation
Build and execute `src/preprocess.py` to extract Lunar South Pole baseline metrics and construct the aligned $0.05^\circ$ terrestrial feature table.

```powershell
# Create outputs directory and run preprocessing pipeline (~2-4 minutes on 8 GB RAM)
New-Item -ItemType Directory -Force -Path outputs
python src/preprocess.py
```
* **Checkpoint:** Verify `outputs/lunar_baselines.json` and `outputs/earth_features.parquet` exist and peak RAM stays below $4.5\text{ GB}$.

### Phase 3: ML Scoring, Clustering & Benchmark Validation
Build and execute `src/model.py` to compute default similarity scores, assign geophysical clusters, and verify that known real-world NASA analog sites rank in the top percentiles.

```powershell
python src/model.py
```
* **Scientific Validation Benchmarks (Expected Top Analog Regions):**
  * **McMurdo Dry Valleys, Antarctica** ($77.47^\circ\text{ S}, 162.52^\circ\text{ E}$) — Hyper-arid, permafrost-bearing, low-temperature polar desert.
  * **Haughton Impact Structure, Devon Island, Canada** ($75.38^\circ\text{ N}, 89.68^\circ\text{ W}$) — Polar impact crater morphology and barren rock abundance.
  * **Atacama Desert, Chile** ($23.86^\circ\text{ S}, 69.13^\circ\text{ W}$) — Extreme aridity, high diurnal thermal swing, silicate regolith analog.
  * **Mauna Kea / Hawaii Volcanic Field, USA** ($19.82^\circ\text{ N}, 155.47^\circ\text{ W}$) — Basaltic regolith emissivity and slope/roughness profile.

### Phase 4: Launch Interactive Dashboard
Start the Streamlit application locally to inspect global analog heatmaps and test dynamic weight adjustments.

```powershell
streamlit run src/app.py
```

### Phase 5: NASA Space Apps Submission & Pitch Package
1. **Code & Documentation Freeze:** Push `src/`, `README.md`, `DATA_DOCUMENTATION.md`, and `environment.yml` to your public GitHub repository (keep `data/` in `.gitignore` with download instructions).
2. **30-Second / 7-Slide Pitch Deck:**
   * *Slide 1:* Hook & **ATLAS** mission identity (Team Binary Knights).
   * *Slide 2:* Why single-factor analog selection fails Artemis South Pole readiness.
   * *Slide 3:* Multi-modal NASA/NOAA data fusion architecture (LRO LOLA + Diviner vs. MODIS + ETOPO 2022).
   * *Slide 4:* Machine learning pipeline (masking, Horn slope/TRI, weighted similarity & clustering under 8 GB RAM).
   * *Slide 5:* Scientific validation — ATLAS rediscovering McMurdo Dry Valleys, Devon Island, and Atacama.
   * *Slide 6:* Live Streamlit + Folium interactive demo walkthrough.
   * *Slide 7:* Scalability roadmap to **Mars (MOLA + THEMIS)** and custom lander engineering constraints.

---

## 6. Data Attribution

* **Lunar Reconnaissance Orbiter (LRO) LOLA & Diviner Data:** NASA Planetary Data System (PDS) Geosciences Node, Washington University in St. Louis (`ode.rsl.wustl.edu/moon`).
* **MODIS `MOD11C3` & `MCD12C1` (Version 061):** NASA EOSDIS Land Processes Distributed Active Archive Center (LP DAAC), USGS Earth Resources Observation and Science (EROS) Center (`search.earthdata.nasa.gov`).
* **ETOPO 2022 Global Relief Model:** NOAA National Centers for Environmental Information (NCEI) (`ncei.noaa.gov/products/etopo-global-relief-model`).
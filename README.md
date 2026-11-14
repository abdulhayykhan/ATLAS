# ATLAS: Analog Terrain & Lunar Alignment System

**Team:** Binary Knights
**Event:** NASA Space Apps Challenge 2026 — *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*

> ATLAS measures the four planned permanent Moon base sites — **Peary, Shackleton, de Gerlache and Amundsen** — directly from NASA LRO data (both poles), profiles eight candidate Earth analog sites from Copernicus DEM, NASA POWER and SoilGrids data, and ranks every Earth site against every Moon base with a transparent weighted dissimilarity score. A Mars quick-look (Jezero Crater, MOLA) runs on the same method.

## What is built and working

| Piece | File | Status |
|---|---|---|
| Moon profiles — all 4 bases: elevation, slope, roughness, PSR %, sun %, Earth %, temperature | `src/preprocess_moon.py` → `outputs/moon_profiles.csv` | ✅ run, verified |
| Earth profiles — 8 sites: terrain (30 m DEM), temperature, soil | `src/preprocess_earth.py` → `outputs/earth_profiles.csv` | ✅ run |
| Mars quick-look — Jezero Crater terrain | `src/preprocess_mars.py` → `outputs/mars_profiles.csv` | ✅ run |
| Scoring & ranking (32 base×site pairs) + radar plots | `src/model.py` → `outputs/scores_ranking.csv`, `outputs/radar_*.png` | ✅ run |
| Interactive app (map, compare, downloads) | `src/app.py` | ✅ |
| Methodology, formula, weights, limitations | `outputs/methodology.md` | ✅ |
| Full dataset documentation | `DATA_DOCUMENTATION.md` | ✅ |

## Quick start

```bash
bash scripts/download_data.sh          # ~2.3 GB, all public NASA/ESA sources, no login
pip install -r requirements.txt        # or: conda env create -f environment.yml
python src/preprocess_moon.py          # ~15 s
python src/preprocess_earth.py         # terrain + NASA POWER + SoilGrids (streams soil, takes longer)
python src/preprocess_mars.py          # ~5 s (HTTP-range window of one MOLA tile)
python src/model.py
streamlit run src/app.py
```

Raw data goes in `data/` (git-ignored, >100 MB files). The app reads only the small files in `outputs/`.

## Data at a glance

- **Moon terrain (LOLA, PDS):** LDEM 80 m, LDSM 240 m slope, LDRM 240 m roughness — **80S/75S and 80N/75N** (the North Pole / Peary is fully covered; there is no "south-only" shortcut).
- **Moon light (PGDA Product 69):** average solar visibility + average Earth visibility, 60 m polar sets + 120 m 75S set for Amundsen; PSR masks LPSR 81S/81N.
- **Moon temperature (Diviner PCP):** polar-south **and** polar-north bolometric tables, winter slice (slon01) + opposite season (slon48). The Diviner *cylindrical* soil-temperature/rock-abundance maps cover only −60°…+60° and contain no data at any polar base — they are **not** used (see `DATA_DOCUMENTATION.md`).
- **Earth:** Copernicus DEM GLO-30 (30 m — fine enough to see a 1.2 km crater; a 5.6 km grid is not), NASA POWER climatology, SoilGrids 2.0 soil.
- **Mars:** MGS MOLA MEGDR, Jezero window fetched by HTTP range (no 130 MB tile download).

## Scoring in one paragraph

Variables (mean slope, % area flatter than 10°, mean temperature, relief, soil/regolith proxy) are min–max normalised across Moon + Earth together; dissimilarity is weighted Euclidean distance (slope 30%, flat area 20%, temperature 20%, soil 15%, relief 15%); **Analog Score = 100·exp(−D)**. Sun % and Earth % are shown as mission context but never scored — Earth has no counterpart. Full method, validation (including the slope-product no-data trap and the north-pole grid handedness, both caught and fixed during development) and stated limitations: `outputs/methodology.md`.

## Repository structure

```text
ATLAS/
├── README.md
├── DATA_DOCUMENTATION.md        # every dataset: source, coverage, size, role, warnings
├── requirements.txt / environment.yml
├── scripts/download_data.sh
├── src/
│   ├── atlas_common.py          # PDS3 label parsing + polar-stereographic ROI engine
│   ├── preprocess_moon.py       # Phase 2A: 4 lunar base profiles
│   ├── preprocess_earth.py      # Phase 2B: 8 Earth site profiles
│   ├── preprocess_mars.py       # Mars (Jezero) quick-look
│   ├── model.py                 # Phase 3: scoring, ranking, radar plots
│   └── app.py                   # Phase 4: Streamlit dashboard
├── outputs/                     # CSVs, radar plots, hillshades, methodology.md
└── data/                        # raw datasets (git-ignored)
```

## Data attribution

LRO LOLA & Diviner: NASA Planetary Data System, Geosciences Node (Washington University in St. Louis) and PGDA (NASA GSFC). Copernicus DEM GLO-30: © European Space Agency / Copernicus, via AWS Open Data. NASA POWER: NASA Langley Research Center. SoilGrids 2.0: © ISRIC — World Soil Information (CC BY 4.0). MGS MOLA MEGDR: NASA PDS.

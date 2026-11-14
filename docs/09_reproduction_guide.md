# Reproduction Guide — ATLAS From Zero

*Anyone with this repository and an internet connection can rebuild every
number in `outputs/` by following these steps in order.*

---

## 1. Environment

```bash
python3 -m venv venv && source venv/bin/activate     # a venv is required on
                                                     # PEP-668-managed systems
pip install -r requirements.txt
# or: conda env create -f environment.yml
```

Key dependencies: `numpy`, `pandas`, `rasterio` (Earth/COG side),
`scikit-learn` (clustering), `matplotlib` (radar plots), `streamlit`,
`folium`, `streamlit-folium`, `plotly`, `pillow`, `pyarrow`.

Note: the Moon pipeline deliberately does **not** depend on GDAL's PDS
support — `src/atlas_common.py` parses PDS3 labels itself — so the limited
GDAL builds shipped with many rasterio wheels are sufficient.

## 2. Download the data (~2.3 GB, all public, no accounts)

```bash
bash scripts/download_data.sh
```

Produces the `data/` tree documented in
`02_phase1_data_acquisition.md`. Interrupt-safe (`curl -C -` resume).
SoilGrids and NASA POWER are streamed later, per site — nothing else to fetch.

*Development note:* any directory with the same layout works as the data
root; the scripts take it as an optional first argument
(`python src/preprocess_moon.py /path/to/data`), defaulting to `./data`.

## 3. Run the pipeline in order

```bash
python src/preprocess_moon.py     # ≈15 s  → outputs/moon_profiles.csv, hillshade_*.png
python src/preprocess_earth.py    # ≈30–50 min for 14 sites (SoilGrids streaming;
                                  #  parallelise with the subset form below)
python src/preprocess_mars.py     # ≈5 s   → outputs/mars_profiles.csv
python src/model.py               # ≈5 s   → outputs/scores_ranking.csv, radar_*.png,
                                  #          regime column in earth_profiles.csv
streamlit run src/app.py
```

Parallel Earth runs (as used for the shipped outputs):

```bash
python src/preprocess_earth.py data 0,1,2,3,4    part_a.csv &
python src/preprocess_earth.py data 5,6,7,8,9    part_b.csv &
python src/preprocess_earth.py data 10,11,12,13  part_c.csv &
# then concatenate part_a/b/c.csv (in that order) into outputs/earth_profiles.csv
# BEFORE running model.py — model.py adds the regime column to that file.
```

## 4. Expected outputs — acceptance numbers

A correct reproduction produces these headline values (small deviations in
the last decimal can occur if a source republishes a product):

**Moon** (`outputs/moon_profiles.csv`, 4 rows × 35 cols): Shackleton slope
19.42°, PSR 33.3%; Peary elevation −1262.7 m, Earth visibility 38.2%;
seasonal mean temperatures between −184.4 °C (de Gerlache) and
−223.8 °C (Peary).

**Earth** (`outputs/earth_profiles.csv`, 14 rows): Etosha relief 0.7 m;
Klyuchevskaya elevation max ≈4846 m; three NaN soil rows (Erebus,
Deception Island, Etosha).

**Scores** (`outputs/scores_ranking.csv`, 56 rows): #1 matches —
Shackleton→Klyuchevskaya 69.7; de Gerlache→Erebus 72.1; Peary→Elgygytgyn
63.1; Amundsen→Erebus 62.7.

**Mars** (`outputs/mars_profiles.csv`, 1 row): Jezero slope 2.92°,
93.1% of area < 10°.

**App:** all six pages load; AppTest reports zero exceptions.

If your Shackleton PSR is ≈24.7% or your Peary elevation ≈−593 m, you have
reproduced two known traps instead (wrong centre / unflipped north grid) —
see `03_phase2a_moon_processing.md`, Steps 2A.3–2A.4 and Step 0.3.1 of the
Phase 0 doc. Those wrong numbers are useful: they prove your pipeline is
otherwise identical to ours up to the corrections.

## 5. Troubleshooting (every row happened during this build)

| Symptom | Cause | Fix |
|---|---|---|
| `pip install` refused system-wide | PEP-668 externally-managed Python | Use the venv in §1 |
| rasterio cannot open `.img` files | Bundled GDAL lacks the PDS driver | Expected — Moon code never asks GDAL to; if *your* added code does, parse labels via `atlas_common.py` |
| SoilGrids reads fail with SSL errors | Proxy + VRT service | `rasterio.Env(GDAL_HTTP_UNSAFESSL="YES")` (already in the code) |
| SoilGrids window lands in the wrong place | SoilGrids CRS is Interrupted Goode Homolosine, not EPSG:4326 | `transform_bounds` before windowing (already in the code) |
| Soil step takes minutes per site | Remote tile streaming | Normal; use the parallel subset form in §3 |
| USGS Mars mosaic returns 403 | Server blocks scripted access | Use the PDS MEGDR range-request path (`preprocess_mars.py`) |
| Peary profile looks like a shallow bowl / Earth-vis ≈21% | North grid read with the southern row convention | Pole-aware mapping in `atlas_common.py` (already fixed) |
| Slope histogram spikes at one value | LDSM DN 0 is no-data | Excluded in `atlas_common.roi_values` (already fixed) |
| A volcano profiles as a flat plain | Site centre off the feature (Klyuchevskaya was 0.6° off) | Verify centre against the DEM maximum/extremes before profiling |
| Streamlit warns about `use_container_width` | Deprecated argument | App uses `width="stretch"` (already fixed) |

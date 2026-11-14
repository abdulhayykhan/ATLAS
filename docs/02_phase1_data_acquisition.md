# Phase 1 — Data Acquisition

*Goal: download every dataset the pipeline uses — all public, no login, no
scraping — verify each file byte-for-byte against its expected size, and lay
it out so the processing phase never has to think about sources again.*

Everything in this phase is automated by **`scripts/download_data.sh`**
(~2.3 GB total). The layout it produces:

```
data/
├── moon/
│   ├── terrain_s/   LOLA GDR IMG+LBL (80S / 75S)
│   ├── terrain_n/   LOLA GDR IMG+LBL (80N / 75N)
│   ├── psr/         LPSR masks (81S / 81N)
│   ├── illum/       PGDA-69 AVGVISIB IMG+LBL
│   └── temperature/ Diviner PCP .tab + .lbl (pols / poln)
└── earth/
    └── terrain/     Copernicus DEM GLO-30 GeoTIFFs (one per site)
```

SoilGrids and NASA POWER are **not** downloaded: they are streamed per site
in Phase 2B (SoilGrids is far too large to mirror; POWER is an API).

---

## Step 1.1 — Moon terrain, both poles (NASA PDS Geosciences Node)

Base URL: `https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/`

| File | Bytes (verified) | Content |
|---|---|---|
| `ldem_80s_80m.img` + `.lbl` | 115,520,000 | Elevation, south polar cap, 80 m/px |
| `ldem_80n_80m.img` + `.lbl` | 115,520,000 | Elevation, north polar cap, 80 m/px |
| `ldsm_75s_240m.img` + `.lbl` | 29,062,688 | Slope, south, 240 m/px |
| `ldsm_75n_240m.img` + `.lbl` | 29,062,688 | Slope, north, 240 m/px |
| `ldrm_75s_240m.img` + `.lbl` | 29,062,688 | Roughness, south, 240 m/px |
| `ldrm_75n_240m.img` + `.lbl` | 29,062,688 | Roughness, north, 240 m/px |

Why these and not the 5 m PGDA-81 mosaic: same instrument (LOLA), both
poles, Amundsen covered, ~0.9 GB instead of ~9 GB, and the PDS detached-label
format is fully self-describing (Phase 2A parses the labels, so no external
metadata can drift out of sync).

## Step 1.2 — Permanently shadowed region masks (PDS extras)

Base URL: `…/extras/illumination/release_2011/img/`

| File | Bytes (verified) | Content |
|---|---|---|
| `lpsr_81s_240m.img` + `.lbl` | ≈9.3 MB | PSR mask, south, 240 m/px |
| `lpsr_81n_240m.img` + `.lbl` | ≈9.3 MB | PSR mask, north, 240 m/px |

Post-download sanity check (Phase 2A): the binary contains only the two
documented DN states (±20000) with no zero fill — i.e. the mask is complete
over the cap, not partially rendered.

## Step 1.3 — Illumination and Earth visibility (PGDA Product 69)

Host: `http://imbrium.mit.edu/EXTRAS/ILLUMINATION/IMG/` (located by reading
the PGDA-69 product page's own HTML — the files are not linked from the PDS
tree).

| File | Bytes (verified) | Used for |
|---|---|---|
| `AVGVISIB_85S_060M_201608.IMG` + `_EARTH.IMG` (+LBL) | 51,166,728 each | Shackleton, de Gerlache — average solar / Earth visibility, 60 m |
| `AVGVISIB_75S_120M_201608.IMG` + `_EARTH.IMG` (+LBL) | 116,250,752 each | Amundsen — 120 m set (the 60 m set does not reach 84.5° S) |
| `AVGVISIB_85N_060M_201608.IMG` + `_EARTH.IMG` (+LBL) | 51,166,728 each | Peary — 60 m |

Values are 18.6-year average visibility fractions stored as DN × 0.00004
(scaling lives in each file's label and is applied by the Phase 2A parser,
not hard-coded blindly — the factor is read from the label).

## Step 1.4 — Temperature: Diviner PCP polar tables (NASA PDS)

Base URL: `https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/diurnal/slon/`

| File | Bytes (verified) | Content |
|---|---|---|
| `pols/…slon01….tab` | 181,213,072 | South polar bins, winter solar-longitude slice |
| `pols/…slon48….tab` | 176,744,648 | South polar bins, opposite-season slice |
| `poln/…slon01….tab` | 235,131,520 | North polar bins, winter slice |
| `poln/…slon48….tab` | 236,353,587 | North polar bins, opposite-season slice |

**Explicitly not downloaded:** the Diviner cylindrical soil-temperature and
rock-abundance maps. They span −60°…+60° latitude only; at the poles they
contain no data at all (Phase 0, Step 0.6). Downloading them anyway was the
single largest waste (~830 MB) in the team's first plan.

## Step 1.5 — Earth terrain tiles (Copernicus DEM GLO-30, ESA via AWS)

URL pattern:
`https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_<TILE>_DEM/Copernicus_DSM_COG_10_<TILE>_DEM.tif`

Tile naming is the 1°×1° cell containing the site's study-box centre:
latitude band = `floor(lat)` (N or S + two digits), longitude band =
`floor(lon)` (E or W + three digits). Example: the Atacama control site at
(−23.86, −69.13) → lat band −24 → `S24`, lon band −70 → `W070`.

Discovery-run tiles (classic-run tiles are listed in
`04_phase2b_earth_processing.md`):

```
N30_00_E058_00  N37_00_E094_00  N40_00_E102_00  S19_00_E016_00
S30_00_W066_00  S78_00_E167_00  S63_00_W061_00  N56_00_E160_00
S19_00_E144_00  N33_00_E126_00  N70_00_E068_00  N67_00_E172_00
N19_00_E076_00  N22_00_W011_00
```

Typical size 10–45 MB per tile. Small outliers are meaningful, not errors:
the Deception Island tile (S63) is 3.2 MB because it is almost all ocean;
the Erebus tile (S78_E167) is 9.1 MB for the same reason. Both were opened
and inspected before use.

## Step 1.6 — Mars terrain (no bulk download)

The Jezero window is fetched by HTTP **range requests** against a single
PDS MOLA MEGDR tile (`megt44n000hb`) during Phase 2C itself — ~3 MB read
out of a 130 MB tile, nothing stored. See `05_phase2c_mars_processing.md`.

## Step 1.7 — Verification protocol applied to every file

1. **Byte size** compared against the server's content length / the expected
   sizes in the table above. A short file is a failed download, not a small
   dataset — re-fetch, never proceed.
2. **Labels present**: every IMG has its detached `.lbl` beside it; the
   Phase 2A parser refuses to guess geometry.
3. **Open test**: each raster family was opened once and sampled before the
   full pipeline ran (this is how the Deception/Erebus small-tile question
   and the LPSR DN check were settled).

## Phase 1 exit criteria — all met

- [x] All Moon terrain/PSR/illumination/temperature files present, sizes verified
- [x] All Earth DEM tiles present and open-tested
- [x] `scripts/download_data.sh` reproduces the whole tree from scratch
- [x] No dataset downloaded "just in case" (the 830 MB cylindrical Diviner
      maps are the documented counterexample)

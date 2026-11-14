# Phase 2A — Moon Processing (`src/atlas_common.py`, `src/preprocess_moon.py`)

*Goal: turn four binary product families into one trustworthy profile per
base — elevation, slope, roughness, shadow, sunlight, Earth visibility and
temperature — with every geometric assumption validated against the terrain
itself. Output: `outputs/moon_profiles.csv` + four hillshade PNGs. Runtime
≈15 seconds.*

---

## Step 2A.1 — Read PDS3 files without a PDS driver

Rasterio's bundled GDAL in this environment has **no PDS driver** and no
Python `osgeo` bindings, so the `.img` files cannot be opened the usual way.
`atlas_common.py` therefore parses each detached PDS3 label directly and
reads the binary with NumPy. Label fields consumed:

- `LINES`, `LINE_SAMPLES`, `SAMPLE_BITS` (16-bit signed, big-endian),
  `SAMPLE_TYPE`
- `SCALING_FACTOR`, `OFFSET`
- Map projection: `MAP_SCALE` (m/px), `CENTER_LATITUDE`,
  `LINE_PROJECTION_OFFSET`, `SAMPLE_PROJECTION_OFFSET`

Value reconstruction: `value = DN × SCALING_FACTOR + OFFSET` — **with one
documented exception**: in the LDEM labels, the field named `OFFSET` is the
reference radius, not an additive offset; elevation is `DN × 0.5`. This is
handled as a special case in the parser and is the first of several places
where reading the label *text* mattered more than assuming the format.

Per-product validity rules (all discovered by inspecting real data, not
assumed):

| Product | Valid DN | Rule |
|---|---|---|
| LDEM | −16000…16000 | no fill value present in polar data |
| LDSM | DN > 0 | **DN 0 is no-data** — Step 2A.4 |
| LDRM | 0…32767 | label `MISSING_CONSTANT = −32768` excluded |
| LPSR | DN = ±20000 only | binary mask, verified clean |
| AVGVISIB | DN × 0.00004 | fraction 0–1 |

## Step 2A.2 — Planetocentric lat/lon → pixel (polar stereographic)

For a base at planetocentric latitude φ and longitude λ, with the Moon's
radius R = 1737.4 km and the grid true at the pole:

```
ρ = 2R · tan(π/4 − |φ|/2)
x = ρ · sin(λ)          y = −ρ · cos(λ)        (south-pole convention)
col = SAMPLE_OFF + x / scale
row = LINE_OFF  + y / scale
```

A circular region of interest (ROI) is cut around (row, col) at the base's
study radius: **Shackleton 15 km, de Gerlache 20 km, Peary 40 km,
Amundsen 60 km**.

## Step 2A.3 — The north-pole handedness discovery (the phase's hardest bug)

The formula above, applied unchanged to the north grids, produced a Peary
profile that contradicted the literature (a shallow, oddly-placed floor) and
an Earth-visibility of 21.4%. Rather than tune the model, the geometry was
tested directly against the terrain it claims to describe:

**Crater-depression test.** For a set of named craters at *known*
coordinates, sample the DEM at the crater centre and in a surrounding ring.
A true centre must sit in a local elevation **low** (the bowl); a mirrored
or rotated mapping puts the "centre" on a rim or wall and fails.

- North candidates tested: Rozhdestvenskiy (and its satellite craters W/U),
  Byrd, Sylvester, Peary.
- South candidates tested: Amundsen, Shoemaker, Faustini, Haworth,
  Sverdrup, de Gerlache.

Four sign conventions were scored for the north grid. The winner —
`row = LINE_OFF − y / scale`, i.e. **the north grids are stored with the
opposite row handedness to the south grids** — scored a combined depression
of **7428 m** against **2051 m** for the next best convention. The parser is
now pole-aware (`lat < 0 → +y; lat > 0 → −y`).

Consequence of the fix: Peary's profile changed completely — mean elevation
−593 m → **−1262.7 m**, Earth visibility 21.4% → **38.2%** — into a deep,
flat crater floor (72.7% of the ROI flatter than 10°), matching published
descriptions of Peary. **Any pipeline that uses one convention for both
poles silently profiles a mirrored location at one of them.**

## Step 2A.4 — The LDSM no-data trap

A first slope run produced an absurd slope distribution: a huge spike at
exactly one value. Inspection showed **DN = 0 occupies ~29% of the polar
cap** while DN > 0 occupies ~0.001% outside real slopes — DN 0 is the
product's no-data marker, not a slope of 45°. Cross-check: at DN-0 pixels,
gradients computed independently from the LDEM give ordinary ~9.7° slopes.
All LDSM statistics now exclude DN 0 (`exclude_raw` in the ROI reader).
Effect on Amundsen: mean slope corrected 15.21° → **10.26°**.

## Step 2A.5 — Per-base terrain, shadow and light statistics

For each base, over its ROI:

- **LDEM:** mean, median, std (= the *relief* variable used in scoring),
  p10, p90, min, max elevation.
- **LDSM:** mean, median, std, p10, p90 slope; % of valid pixels with
  slope < 5° and < 10° (the < 10° fraction is the scoring *flat-area*
  variable).
- **LDRM:** mean and p90 roughness.
- **LPSR:** % of ROI pixels flagged permanently shadowed.
- **AVGVISIB:** mean solar visibility % and mean Earth visibility %
  (60 m sets for Shackleton, de Gerlache, Peary; the 120 m 75S set for
  Amundsen, whose latitude is outside the 85S frame).
- **Hillshade PNG** rendered from the LDEM ROI for visual verification
  (this is the check that caught Shackleton's centre — Step 0.3.1).

## Step 2A.6 — Temperature from Diviner PCP tables

The PCP `.tab` files are ~180–236 MB of binned polar observations; they are
**streamed in 400,000-row chunks** (never loaded whole) and filtered by
haversine distance from the base centre on the Moon (R = 1737.4 km) to the
ROI radius. For each base and each seasonal slice — slon01 (local winter)
and slon48 (opposite season):

- mean bolometric temperature (K),
- **cold level = 1st percentile** of bins, *not* the raw minimum.

Why percentile: the raw bin minimum in the Amundsen ROI is a single 12.2 K
bin — an outlier orders of magnitude below its neighbours. Reported cold
levels (1st percentile, 34–39 K across the bases) match Diviner's published
polar cold-trap range; the raw minimum does not.

Derived columns: seasonal mean of the two slices (K and °C — the °C value is
the scoring *temperature* variable), and seasonal range (K).

## Step 2A.7 — Final base profiles (measured values)

| Measure | Peary | Shackleton | de Gerlache | Amundsen |
|---|---|---|---|---|
| Centre | 88.63N, 24.4E | 89.67S, 129.78E | 88.5S, 87.1W | 84.5S, 82.8E |
| ROI radius (km) | 40 | 15 | 20 | 60 |
| Mean elevation (m) | −1262.7 | 110.2 | −239.2 | −1622.2 |
| Relief — elev std (m) | 366.5 | 1159.3 | 926.7 | 1782.2 |
| Mean slope (°) | 7.97 | 19.42 | 13.11 | 10.26 |
| Area < 10° (%) | 72.7 | 19.5 | 33.1 | 54.2 |
| Roughness mean (m) | 0.79 | 1.11 | 0.87 | 1.07 |
| PSR area (%) | 10.5 | 33.3 | 19.7 | 7.7 |
| Sun visibility (%) | 12.4 | 17.7 | 18.3 | 19.9 |
| Earth visibility (%) | 38.2 | 22.6 | 21.0 | 27.0 |
| Winter mean temp (K) | 55.7 | 63.5 | 75.4 | 76.1 |
| Winter cold, p1 (K) | 34.0 | 40.7 | 36.6 | 35.0 |
| Opposite-season mean (K) | 42.9 | 88.2 | 102.0 | 68.4 |
| Seasonal mean temp (°C) | −223.8 | −197.3 | −184.4 | −200.8 |

Reading the table: Shackleton is the steep, shadow-rich crater the
literature describes (only 19.5% of its ROI is rover-friendly flat, a third
is permanently shadowed); Peary is the gentlest, most Earth-visible site —
exactly the character that made both famous as candidate bases. The profiles
agree with published base character *before* any scoring uses them.

## Phase 2A exit criteria — all met

- [x] Geometry validated by crater-depression tests at both poles
- [x] No-data conventions verified per product against independent gradients
- [x] Hillshades visually confirm every ROI is centred on its crater
- [x] Temperature cold levels reported as percentiles, outliers documented
- [x] Output: one row per base, 35 measured columns, sources cited in-row

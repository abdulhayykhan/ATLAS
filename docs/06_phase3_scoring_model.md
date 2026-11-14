# Phase 3 — Scoring, Ranking and Clustering (`src/model.py`)

*Goal: turn two profile tables into defensible rankings. Every choice in
this phase was fixed **before** the discovery data was seen, and the formula
is published in the app. Outputs: `outputs/scores_ranking.csv` (56 rows),
`outputs/radar_<base>.png` ×4, and the `regime` column added to
`outputs/earth_profiles.csv`. Runtime ≈5 seconds.*

---

## Step 3.1 — Variables

Five pillars, each present on both sides of the comparison (or honestly
proxied, where marked):

| Pillar | Moon value | Earth value | Weight |
|---|---|---|---|
| Slope | LDSM mean slope (°) | DEM mean slope (°) | **30%** |
| Flat area | % of ROI with slope < 10° | % of box with slope < 10° | **20%** |
| Temperature | Diviner seasonal mean (°C) | POWER annual mean (°C) | **20%** |
| Soil / regolith | — (proxy, below) | SoilGrids-derived index | **15%** |
| Relief | LDEM elevation std (m) | DEM elevation std (m) | **15%** |

**Deliberately not scored:** sun visibility % and Earth visibility %. Earth
has no counterpart for either; inventing one would fabricate two-fifths of
every score. Both are displayed as mission context on the Moon Bases page.

**The soil proxy, stated plainly:** no dataset gives lunar soil percentages
at these bases, so the soil pillar is an *Earth-side regolith-likeness
index* — `(coarse fragments + sand − clay)`, min–max normalised — scored as
distance from an ideal regolith (index 1). It is identical for every base
and labelled a proxy in the code, the methodology and the app.

## Step 3.2 — Normalisation

Each pillar is min–max normalised to 0–1 across **Moon bases and Earth
sites together**:

```
x_norm = (x − min) / (max − min)        over the combined set
```

One common scale is what makes a weighted Euclidean distance between a Moon
row and an Earth row meaningful. (Guide Question 3 asks exactly this; the
complementary rule — comparing ROI *statistics*, never pixel-to-pixel
across the 30 m / 240 m resolution gap — is in the methodology.)

## Step 3.3 — Dissimilarity and Analog Score

For base *b* and site *s*, with per-pillar normalised differences
`d_k = |x_norm(b,k) − x_norm(s,k)|`:

```
D(b,s) = sqrt( Σ_k w_k · d_k²  /  Σ_k w_k )          (weighted Euclidean)
Analog Score = 100 · exp(−D)                          (100 = identical)
```

Per-pillar distances `dist_slope, dist_flat, dist_temperature, dist_relief,
dist_soil` are stored for every pair — they power the radar plots, the
top/weakest-factor labels, and the app's live re-weighting (Phase 4).

## Step 3.4 — The missing-data rule

If a site's soil values are missing (SoilGrids gaps: Antarctica, Etosha
Pan), its soil weight is set to 0 and the remaining weights are
renormalised by their sum (the `Σ w_k` denominator above). A site is never
punished for a dataset's coverage hole. This rule exists because the
control run's first version silently scored McMurdo's missing soil as 0 —
the fix changed its ranking, which is how we know the rule matters.

## Step 3.5 — Validation: the control run (classic sites)

Same code, classic pool (Phase 2B, Step 2B.2). Untuned result:

| Base | Control-run #1 | Score |
|---|---|---|
| Shackleton | McMurdo Dry Valleys | 65.5 |
| de Gerlache | McMurdo Dry Valleys | 70.2 |
| Amundsen | McMurdo Dry Valleys | 59.2 |
| Peary | Atacama Desert | 64.3 |

McMurdo Dry Valleys is the literature's canonical lunar analog and Atacama
its canonical hyper-arid analog. An engine that rediscovers both, blind,
has earned the right to have its *novel* rankings taken seriously — this is
the project's validation evidence (Guide Question 7).

## Step 3.6 — Discovery-run results (novel sites)

Top 3 per base, default (balanced) weights:

| Base | #1 (score) | #2 (score) | #3 (score) |
|---|---|---|---|
| Shackleton | **Klyuchevskaya Volcanic Group** (69.7) | Mount Erebus (67.4) | Deception Island (59.8) |
| de Gerlache | **Mount Erebus** (72.1) | Klyuchevskaya (69.5) | Deception Island (65.8) |
| Peary | **Elgygytgyn Crater** (63.1) | Lut Desert (61.5) | Qaidam Basin (61.5) |
| Amundsen | **Mount Erebus** (62.7) | Klyuchevskaya (60.4) | Badain Jaran (56.1) |

Why these make physical sense (the model's story, in terrain terms):

- The three south-pole bases are steep, high-relief, cold places; the
  winners are Earth's steep, high-relief, cold volcanic terrains.
  Erebus adds the polar-volcanic combination no classic analog offers.
- Peary is the flattest, gentlest base (72.7% < 10°, relief 367 m); its
  winner is a flat-floored polar impact crater, and the runners-up are the
  two flattest cold basins in the pool.
- The temperature pillar is the weakest factor for nearly every winner —
  the documented #1 limitation (no Earth site approaches −184…−224 °C);
  rankings are decided by the terrain pillars, which is where an analog's
  testing value actually lives.

## Step 3.7 — Regime clustering (Guide Objective 4)

K-Means (k = 3, `n_init=10`, seed 42) over the Earth sites' normalised
features (slope, flat, temperature, relief, regolith index) groups the pool
into environmental regimes. Labels are **derived mechanically**, never
hand-assigned: regimes are numbered by their cluster-mean temperature
(1 = coldest) with a slope word from the centroid ("rugged" if centroid
slope_n > 0.6, "flat" if < 0.25) and the cluster-mean temperature printed in
the label itself.

| Regime | Members |
|---|---|
| Regime 1 · rugged (cluster mean −4 °C) | Badain Jaran, Mount Erebus, Deception Island, Klyuchevskaya |
| Regime 2 · flat (cluster mean 14 °C) | Undara, Manjanggul (Jeju), Elgygytgyn, Lonar |
| Regime 3 · flat (cluster mean 16 °C) | Lut, Qaidam, Etosha, Salinas Grandes, Yamal, Tenoumer |

Two earlier naming schemes were tried and **rejected** because they
mislabelled individual members (a cluster's name is a statement about its
centroid, not about every member — Yamal sits in Regime 3 on terrain
character despite its Arctic cold). The shipped labels say only what the
centroid supports, with the mean temperature visible so a reader can judge.

## Step 3.8 — Radar plots

For each base's #1 site, a polar plot of per-pillar similarity
(`1 − dist_k`) across Slope / Flat area / Temperature / Relief / Soil
proxy, saved as `outputs/radar_<base>.png` and shown in the app's Compare
page when the displayed site is the base's top match. A pillar that was
dropped for missing data is drawn at the neutral 0.5 and the methodology
says so.

## Phase 3 exit criteria — all met

- [x] Formula, weights and normalisation fixed before discovery data seen
- [x] Control run reproduces the literature's classic rankings
- [x] 56 discovery pairs scored; per-pillar distances stored for audit
- [x] Missing-data renormalisation implemented and regression-tested by the
      McMurdo control case
- [x] Clustering shipped with honest, mechanically-derived labels

# Validation & Quality Assurance

*Every claim ATLAS makes was checked by a method other than the one that
produced it. This file is the audit trail.*

---

## V1 — Download integrity
Every Phase 1 file's byte size was compared with the server's expected
size (table in `02_phase1_data_acquisition.md`). Two small Earth tiles
(Deception 3.2 MB, Erebus 9.1 MB) triggered review and were explained by
ocean fraction after opening — not assumed away.

## V2 — Geometry: crater-depression tests (both poles)
Named craters at known coordinates must sit in elevation lows. South set:
Amundsen, Shoemaker, Faustini, Haworth, Sverdrup, de Gerlache — pass under
the standard convention. North set: Rozhdestvenskiy + satellites, Byrd,
Sylvester, Peary — pass **only** under the flipped row convention
(combined depression 7428 m vs 2051 m for the next candidate). This test
caught the north-pole handedness error that no label documents.

## V3 — Visual centring: hillshades
Each base's LDEM hillshade was inspected. Shackleton's first version showed
the bowl displaced from frame centre → root-caused to the widely-quoted
wrong centre (89.9° S, 0° E) → corrected to the IAU centre
(89.67° S, 129.78° E) → hillshade now dead-centre, PSR 24.7% → 33.3%.

## V4 — No-data forensics (LDSM)
The DN-0 spike (~29% of cap) was tested against independent DEM gradients
(~9.7° at DN-0 pixels) before being declared no-data. Amundsen slope moved
15.21° → 10.26° after exclusion — a correction larger than most ranking
gaps, i.e. skipping this check would have poisoned every score.

## V5 — Temperature outlier check (Diviner)
Raw bin minima (a single 12.2 K bin at Amundsen) rejected as outliers;
1st-percentile cold levels (34–39 K) agree with published Diviner polar
cold-trap ranges.

## V6 — Earth profiles vs the features they name
- Etosha Pan relief 0.7 m over 20 km — a salt pan, as named.
- Yamal mean elevation 7.8 m — low tundra plain, as named.
- Klyuchevskaya first profile (mean 51.9 m) **failed** this check against
  "Eurasia's tallest volcano" → DEM-located summit (4,846 m at 56.058° N)
  → centre corrected → re-profiled (mean 2,347.7 m, max 4,845.6 m ✓).
- Jezero slope 2.92°, 93.1% < 10° — matches its selection as a landing site.

## V7 — Engine validation: the control run
The scoring engine, untuned, ranks the literature's canonical analogs at
the top when they are in the pool (McMurdo #1 ×3 bases; Atacama #1 for
Peary). See `06_phase3_scoring_model.md`, Step 3.5. The discovery run's
winners were then examined for physical sense pillar-by-pillar (Step 3.6)
rather than accepted blindly.

## V8 — Missing-data behaviour
Regression case: McMurdo (control run) — soil NaN must renormalise, not
zero-score. Confirmed by ranking change when the rule was introduced, and
the same path now serves Erebus, Deception Island and Etosha.

## V9 — Software tests
- All `src/*.py` compile (`py_compile`).
- Full pipeline re-run end-to-end from the staged data: moon ≈15 s,
  mars ≈5 s, model ≈5 s, earth ≈2–4 min/site (SoilGrids streaming).
- Streamlit AppTest: 6/6 pages zero exceptions; Finder preset interaction
  zero exceptions; local server HTTP 200 with a clean log.

## Known limitations (also in the app — nothing here is hidden)

1. **Temperature gap.** Lunar seasonal means are −184…−224 °C; no Earth
   site is close. Absolute-temperature comparison compresses all scores;
   within-base rankings remain meaningful.
2. **Resolution mismatch.** Moon slope at 240 m baseline vs Earth at 30 m;
   fine Earth detail can only raise Earth slopes — the comparison is
   conservative.
3. **Air vs surface temperature.** POWER is 2 m air climatology; Diviner
   is surface bolometric. Compared as thermal-regime indicators.
4. **Candidate pool, not a global scan.** 14 curated novel sites; the
   ETOPO/MODIS global scan from the team's design document is next.
5. **Cave sites are surface-profiled** with documented cave metadata; no
   underground raster exists in v1 (LiDAR is roadmap).
6. **Volatile-trap layers.** PSR fraction + Diviner cold traps stand in
   for dedicated neutron (LEND) / spectrometer (M³) layers — roadmap.

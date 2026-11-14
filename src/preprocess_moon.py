"""ATLAS Phase 2A — Lunar baseline extraction for ALL FOUR challenge bases.

Reads the staged LRO products (see scripts/download_data.sh) and writes
outputs/moon_profiles.csv — one row per base (Peary, Shackleton, de Gerlache,
Amundsen) with terrain, illumination, shadow and temperature statistics.

Products used (all NASA LRO, via PDS Geosciences Node / LOLA team):
  Terrain      LDEM 80S/80N 80 m DEM, LDSM 75S/75N 240 m slope,
               LDRM 75S/75N 240 m roughness   (PDS IMG + detached labels)
  Shadow       LPSR 81S/81N 240 m permanently-shadowed-region mask
  Illumination AVGVISIB 85S/75S/85N 60-120 m average solar visibility and
               average Earth visibility (PGDA Product 69, Mazarico et al.)
  Temperature  Diviner PCP bolometric temperature tables, polar south (pols)
               AND polar north (poln), winter slice slon01 + opposite-
               season slice slon48 (Williams et al. 2019)

Run:  python src/preprocess_moon.py [data_root]
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atlas_common import BASES, roi_values, stats  # noqa: E402

DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ATLAS_DATA", "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
os.makedirs(OUT, exist_ok=True)
MOON_R = 1737.4  # km


def haversine_moon_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * MOON_R * np.arcsin(np.sqrt(a))


def diviner_roi_stats(tab_path, lat, lon, roi_km, chunksize=400_000):
    """Stream a Diviner PCP .tab (CSV: x, y, clon, clat, tbol) and keep only
    bins inside the ROI — the full tables are 180-235 MB each."""
    kept = []
    for chunk in pd.read_csv(tab_path, chunksize=chunksize):
        chunk.columns = [c.strip() for c in chunk.columns]
        d = haversine_moon_km(lat, lon, chunk["clat"].values, chunk["clon"].values)
        sel = chunk.loc[d <= roi_km, "tbol"]
        if len(sel):
            kept.append(sel.values)
    if not kept:
        return {}
    v = np.concatenate(kept)
    # p1 (1st percentile) is reported as the "cold extreme", not the raw bin
    # minimum: single 240 m PCP bins can be low outliers (e.g. one 12 K bin in
    # the Amundsen ROI), while p1 is a robust measured cold level.
    return {"mean": float(np.mean(v)), "median": float(np.median(v)),
            "p1": float(np.percentile(v, 1)), "p10": float(np.percentile(v, 10)), "n": int(len(v))}


def hillshade_png(dem_img, dem_lbl, base, out_path):
    """Simple shaded-relief PNG of the DEM around a base (for the app/report)."""
    from PIL import Image
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from atlas_common import open_img, latlon_to_pixel
    arr, lbl, scaling, offset = open_img(dem_img, dem_lbl)
    crow, ccol = latlon_to_pixel(lbl, base["lat"], base["lon"])
    r_px = base["roi_km"] * 1000 / lbl["scale_m"]
    r0 = max(0, int(crow - r_px)); r1 = min(lbl["lines"], int(crow + r_px))
    c0 = max(0, int(ccol - r_px)); c1 = min(lbl["samples"], int(ccol + r_px))
    z = np.asarray(arr[r0:r1, c0:c1], dtype=np.float32) * scaling
    gy, gx = np.gradient(z, lbl["scale_m"], lbl["scale_m"])
    slope = np.arctan(np.sqrt(gx ** 2 + gy ** 2))
    aspect = np.arctan2(-gy, gx)
    az, alt = np.radians(315), np.radians(45)
    hs = (np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    img = (np.clip(hs, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img, mode="L").save(out_path)


def main():
    rows = []
    for base in BASES:
        pole = "s" if base["pole"] == "S" else "n"
        lat, lon, roi = base["lat"], base["lon"], base["roi_km"]
        row = {"base_name": base["base_name"], "pole": base["pole"], "lat": lat, "lon": lon,
               "roi_radius_km": roi, "crater_diameter_km": base["crater_diam_km"]}
        tdir = os.path.join(DATA, "moon", f"terrain_{pole}")
        # Elevation (LDEM 80 m)
        dem = os.path.join(tdir, f"ldem_80{pole}_80m")
        s = stats(roi_values(dem + ".img", dem + ".lbl", lat, lon, roi, valid_raw=(-16000, 16000)))
        row.update({f"elev_{k}_m": round(v, 1) for k, v in s.items() if k != "n"})
        # Slope (LDSM 240 m, degrees)
        slp = os.path.join(tdir, f"ldsm_75{pole}_240m")
        v = roi_values(slp + ".img", slp + ".lbl", lat, lon, roi, valid_raw=(-30000, 32766), exclude_raw=(0,))
        s = stats(v)
        row.update({f"slope_{k}_deg": round(v, 2) for k, v in s.items() if k != "n"})
        row["pct_slope_under_5deg"] = round(100 * float(np.mean(v < 5)), 1)
        row["pct_slope_under_10deg"] = round(100 * float(np.mean(v < 10)), 1)
        # Roughness (LDRM 240 m, metres)
        rgh = os.path.join(tdir, f"ldrm_75{pole}_240m")
        s = stats(roi_values(rgh + ".img", rgh + ".lbl", lat, lon, roi, valid_raw=(0, 32767)))
        row["roughness_mean_m"] = round(s.get("mean", np.nan), 2)
        row["roughness_p90_m"] = round(s.get("p90", np.nan), 2)
        # Permanently shadowed fraction (LPSR)
        psr = os.path.join(DATA, "moon", "psr", f"lpsr_81{pole}_240m")
        v = roi_values(psr + ".img", psr + ".lbl", lat, lon, roi, valid_raw=(-20000, 20000))
        row["psr_pct"] = round(100 * float(np.mean(v > 0.5)), 1) if len(v) else np.nan
        # Illumination: 85x 60 m set for the polar bases; Amundsen (84.5S) uses the 75S 120 m set
        if base["base_name"] == "Amundsen":
            tag = "75S_120M"
        elif base["pole"] == "S":
            tag = "85S_060M"
        else:
            tag = "85N_060M"
        for kind, colname in [("", "sun_visibility_pct"), ("_EARTH", "earth_visibility_pct")]:
            f = os.path.join(DATA, "moon", "illum", f"AVGVISIB_{tag}_201608{kind}")
            v = roi_values(f + ".IMG", f + ".LBL", lat, lon, roi, valid_raw=(0, 25000))
            row[colname] = round(100 * float(np.mean(v)), 1) if len(v) else np.nan
        # Temperature: Diviner PCP, winter (slon01) + opposite season (slon48)
        tdir2 = os.path.join(DATA, "moon", "temperature")
        ptag = "pols" if base["pole"] == "S" else "poln"
        temps = {}
        for sl in ["slon01", "slon48"]:
            tab = os.path.join(tdir2, f"pcp_avg_tbol_{ptag}_win_{sl}_240.tab")
            if os.path.exists(tab):
                temps[sl] = diviner_roi_stats(tab, lat, lon, roi)
        if temps.get("slon01"):
            row["temp_winter_mean_k"] = round(temps["slon01"]["mean"], 1)
            row["temp_winter_cold_p1_k"] = round(temps["slon01"]["p1"], 1)
        if temps.get("slon48"):
            row["temp_opposite_mean_k"] = round(temps["slon48"]["mean"], 1)
            row["temp_opposite_cold_p1_k"] = round(temps["slon48"]["p1"], 1)
        if temps.get("slon01") and temps.get("slon48"):
            row["temp_seasonal_mean_k"] = round((temps["slon01"]["mean"] + temps["slon48"]["mean"]) / 2, 1)
            row["temp_seasonal_range_k"] = round(abs(temps["slon48"]["mean"] - temps["slon01"]["mean"]), 1)
        if "temp_seasonal_mean_k" in row:
            row["temp_seasonal_mean_c"] = round(row["temp_seasonal_mean_k"] - 273.15, 1)
        row["sources"] = ("LOLA LDEM/LDSM/LDRM + LPSR (NASA PDS), PGDA-69 AVGVISIB illumination, "
                          "Diviner PCP temperature (NASA PDS)")
        rows.append(row)
        print("done", base["base_name"])
        # Hillshade figure
        try:
            hillshade_png(dem + ".img", dem + ".lbl", base,
                          os.path.join(OUT, f"hillshade_{base['base_name'].replace(' ', '').lower()}.png"))
        except Exception as e:  # figure is a bonus, never block the numbers
            print("hillshade failed for", base["base_name"], e)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "moon_profiles.csv"), index=False)
    print(df.to_string())
    print("Wrote outputs/moon_profiles.csv")


if __name__ == "__main__":
    main()

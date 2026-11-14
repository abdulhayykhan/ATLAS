"""ATLAS Phase 2B — Earth analog site profiles.

For each candidate site (fixed 20 x 20 km box):
  Terrain    Copernicus DEM GLO-30 (30 m, ESA/Copernicus via AWS COG) —
             slope from Horn gradients computed at native resolution, then
             aggregated. This is the fine-resolution second stage that a
             5.6 km ETOPO grid cannot do (Meteor Crater is ~1.2 km wide).
  Temperature NASA POWER climatology API (NASA LaRC) — monthly T2M means,
             annual mean, warmest/coldest month, seasonal range.
  Soil       SoilGrids 2.0 (ISRIC) 0-5 cm via the public VRT service —
             sand %, clay %, coarse fragments % (regolith proxies).

Writes outputs/earth_profiles.csv.
Run:  python src/preprocess_earth.py [data_root]
"""
import json
import os
import sys
import urllib.request

import numpy as np
import pandas as pd

DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ATLAS_DATA", "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
os.makedirs(OUT, exist_ok=True)
BOX_KM = 20.0

# ---------------------------------------------------------------------------
# NOVEL-SITE DISCOVERY SET (Challenge Guide #09, Section 1-2):
# The guide's core task is to discover and rank NOVEL, uncatalogued analogs.
# The world-renowned sites named in the guide and the classic literature —
# Atacama, Mauna Loa / Mauna Kea, Haughton Crater, Rio Tinto, Hawaii, Iceland,
# Mojave, McMurdo Dry Valleys, Meteor Crater, Svalbard — are therefore
# EXCLUDED from this production run (they were used once as a control run to
# validate the engine; see outputs/methodology.md). The pool below was
# assembled to span at least four of the guide's terrain types: arid basins,
# high-altitude volcanic fields, salt flats, subterranean caves, plus
# permafrost terrain and lesser-known impact structures. Coordinates are
# ATLAS study-box centres (20 x 20 km), chosen on the named feature.
# ---------------------------------------------------------------------------
SITES = [
    # --- Arid basins ---
    {"site_name": "Lut Desert (Dasht-e Lut)", "country": "Iran", "lat": 30.60, "lon": 58.70,
     "site_type": "Hyper-arid basin; yardang fields", "terrain_type": "Arid basin",
     "tile": "N30_00_E058_00",
     "analog_note": "Among the hottest land surfaces on Earth (satellite LST >70 C); wind-carved yardangs mirror Martian terrain; almost never used as a formal analog site."},
    {"site_name": "Qaidam Basin", "country": "China", "lat": 37.40, "lon": 94.30,
     "site_type": "High-altitude cold desert basin", "terrain_type": "Arid basin",
     "tile": "N37_00_E094_00",
     "analog_note": "3,000 m cold desert with yardangs, salt lakes and polygonal ground; studied regionally as a Mars analog but absent from global analog catalogues."},
    {"site_name": "Badain Jaran Desert", "country": "China", "lat": 40.10, "lon": 102.20,
     "site_type": "Megadune desert with inter-dune lakes", "terrain_type": "Arid basin",
     "tile": "N40_00_E102_00",
     "analog_note": "Tallest stationary dunes on Earth (~460 m) with >100 permanent lakes; dune-field dynamics relevant to lunar/Martian granular physics; uncatalogued as an analog."},
    # --- Salt flats ---
    {"site_name": "Etosha Pan", "country": "Namibia", "lat": -18.80, "lon": 16.30,
     "site_type": "Ephemeral salt pan", "terrain_type": "Salt flat",
     "tile": "S19_00_E016_00",
     "analog_note": "4,800 km2 clay-salt pan, blinding-white evaporite surface with extreme albedo and desiccation cracking; not a catalogued planetary analog."},
    {"site_name": "Salinas Grandes", "country": "Argentina", "lat": -30.00, "lon": -65.80,
     "site_type": "High salt flat (salar)", "terrain_type": "Salt flat",
     "tile": "S30_00_W066_00",
     "analog_note": "Vast halite crust with polygonal pressure ridges — a surface-process analog for Martian chloride deposits; overshadowed by Bolivian salars in the literature."},
    # --- High-altitude / polar volcanic fields ---
    {"site_name": "Mount Erebus", "mask_water": True, "country": "Antarctica (Ross Island)", "lat": -77.53, "lon": 167.17,
     "site_type": "Polar volcano with persistent lava lake", "terrain_type": "Volcanic field",
     "tile": "S78_00_E167_00",
     "analog_note": "The southernmost active volcano: volcanism inside a polar ice cap, with ice towers and lava-ice interaction — a combined volcanic + PSR-style cold-trap setting no classic analog offers."},
    {"site_name": "Deception Island", "mask_water": True, "country": "Antarctica (South Shetlands)", "lat": -62.97, "lon": -60.70,
     "site_type": "Flooded volcanic caldera, polar", "terrain_type": "Volcanic field",
     "tile": "S63_00_W061_00",
     "analog_note": "Active caldera with geothermal ground and ash-covered glaciers; volcanic-permafrost interaction analogous to Martian polar volcanism; rarely catalogued."},
    {"site_name": "Klyuchevskaya Volcanic Group", "country": "Russia (Kamchatka)", "lat": 56.06, "lon": 160.64,
     "site_type": "Remote subarctic volcanic field", "terrain_type": "Volcanic field",
     "tile": "N56_00_E160_00",
     "analog_note": "Eurasia's tallest active volcano cluster amid ash plains and lahar fields; extremely remote and under-studied as an analog despite classic basaltic terrain."},
    # --- Subterranean caves / lava tubes (surface box + documented cave system) ---
    {"site_name": "Undara Lava Tubes", "country": "Australia (Queensland)", "lat": -18.20, "lon": 144.60,
     "site_type": "Lava tube system in basalt flow field", "terrain_type": "Subterranean cave",
     "tile": "S19_00_E144_00",
     "analog_note": "One of the world's longest lava-tube systems (~160 km of tubes from a single shield volcano) — a direct structural analog for lunar lava tubes proposed as radiation-shielded habitats."},
    {"site_name": "Manjanggul Lava Tube (Jeju)", "mask_water": True, "country": "South Korea", "lat": 33.47, "lon": 126.77,
     "site_type": "Multi-level lava tube, volcanic island", "terrain_type": "Subterranean cave",
     "tile": "N33_00_E126_00",
     "analog_note": "7.4 km multi-storey lava tube with lava columns; Jeju's tube systems are UNESCO-listed but absent from planetary analog catalogues."},
    # --- Permafrost / polar terrain ---
    {"site_name": "Yamal Peninsula (Bovanenkovo)", "country": "Russia (Siberia)", "lat": 70.40, "lon": 68.50,
     "site_type": "Continuous permafrost; gas-emission craters", "terrain_type": "Permafrost terrain",
     "tile": "N70_00_E068_00",
     "analog_note": "Ice-rich permafrost that has produced explosive gas-emission craters since 2014 — a live process analog for volatile-driven surface change on the Moon and Mars."},
    {"site_name": "Elgygytgyn Crater", "country": "Russia (Chukotka)", "lat": 67.50, "lon": 172.08,
     "site_type": "Polar impact crater lake", "terrain_type": "Impact structure",
     "tile": "N67_00_E172_00",
     "analog_note": "18 km impact crater in Arctic permafrost, never glaciated; combines impact geology with polar volatile terrain — an almost unknown counterpart to Haughton."},
    # --- Lesser-known impact structures ---
    {"site_name": "Lonar Crater", "country": "India", "lat": 19.98, "lon": 76.51,
     "site_type": "Impact crater in basalt (Deccan Traps)", "terrain_type": "Impact structure",
     "tile": "N19_00_E076_00",
     "analog_note": "One of the only impact craters excavated in basaltic lava — the closest terrestrial process match to craters in lunar maria and Martian lava plains."},
    {"site_name": "Tenoumer Crater", "country": "Mauritania (Sahara)", "lat": 22.92, "lon": -10.40,
     "site_type": "Fresh impact crater in desert basement", "terrain_type": "Impact structure",
     "tile": "N22_00_W011_00",
     "analog_note": "Near-perfectly preserved 1.9 km crater in remote Sahara; pristine ejecta and almost no human disturbance — an uncatalogued fresh-crater analog."},
]

# Classic, already-catalogued analogs — deliberately EXCLUDED from the
# discovery run per Challenge Guide #09 (used only in the validation control).
CLASSIC_SITES_EXCLUDED = ["Atacama Desert", "Mauna Loa / Mauna Kea (Hawaii)",
                          "Haughton Crater", "Rio Tinto", "Iceland Volcanic Fields",
                          "Mojave Desert", "McMurdo Dry Valleys", "Meteor Crater",
                          "Svalbard (Adventdalen)", "Wadi Rum", "Pilbara"]


def box_bounds(lat, lon, km=BOX_KM):
    dlat = (km / 2) / 111.32
    dlon = (km / 2) / (111.32 * max(0.05, np.cos(np.radians(lat))))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def terrain_stats(site):
    import rasterio
    from rasterio.windows import from_bounds
    path = os.path.join(DATA, "earth", "terrain",
                        f"Copernicus_DSM_COG_10_{site['tile']}_DEM.tif")
    if not os.path.exists(path):
        path = ("https://copernicus-dem-30m.s3.amazonaws.com/"
                f"Copernicus_DSM_COG_10_{site['tile']}_DEM/Copernicus_DSM_COG_10_{site['tile']}_DEM.tif")
    with rasterio.Env(GDAL_HTTP_UNSAFESSL="YES"):
        with rasterio.open(path) as src:
            win = from_bounds(*box_bounds(site["lat"], site["lon"]), transform=src.transform)
            z = src.read(1, window=win).astype(np.float32)
            res_x, res_y = src.res
    lat_rad = np.radians(site["lat"])
    dx_m = res_x * 111320 * np.cos(lat_rad)
    dy_m = res_y * 110540
    valid = z > -1000
    if site.get("mask_water"):
        valid &= z > 0.5  # island/coastal sites: drop sea pixels (DEM sea = 0)
    zf = np.where(valid, z, np.nan)
    gy, gx = np.gradient(np.nan_to_num(zf, nan=np.nanmean(zf)), dy_m, dx_m)
    slope = np.degrees(np.arctan(np.sqrt(gx ** 2 + gy ** 2)))
    slope[~valid] = np.nan
    return {
        "elev_mean_m": round(float(np.nanmean(zf)), 1),
        "elev_median_m": round(float(np.nanmedian(zf)), 1),
        "elev_std_m": round(float(np.nanstd(zf)), 1),
        "elev_min_m": round(float(np.nanmin(zf)), 1),
        "elev_max_m": round(float(np.nanmax(zf)), 1),
        "slope_mean_deg": round(float(np.nanmean(slope)), 2),
        "slope_median_deg": round(float(np.nanmedian(slope)), 2),
        "pct_slope_under_5deg": round(100 * float(np.nanmean(slope < 5)), 1),
        "pct_slope_under_10deg": round(100 * float(np.nanmean(slope < 10)), 1),
    }


def power_temperature(site):
    url = ("https://power.larc.nasa.gov/api/temporal/climatology/point"
           f"?parameters=T2M&community=RE&longitude={site['lon']}&latitude={site['lat']}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        data = json.load(r)
    t = data["properties"]["parameter"]["T2M"]
    months = [t[m] for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]]
    months = [m for m in months if m > -900]
    return {
        "temp_mean_c": round(float(t["ANN"]), 1),
        "temp_coldest_month_c": round(min(months), 1),
        "temp_warmest_month_c": round(max(months), 1),
        "temp_seasonal_range_c": round(max(months) - min(months), 1),
    }


def soilgrids(site):
    """Mean 0-5 cm sand/clay/coarse-fragments over the site box via SoilGrids VRTs."""
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.warp import transform_bounds
    out = {}
    names = {"sand": "sand_pct", "clay": "clay_pct", "cfvo": "coarse_fragments_pct"}
    with rasterio.Env(GDAL_HTTP_UNSAFESSL="YES", VSI_CACHE="TRUE"):
        for prop, col in names.items():
            url = f"https://files.isric.org/soilgrids/latest/data/{prop}/{prop}_0-5cm_mean.vrt"
            with rasterio.open(url) as src:
                b = transform_bounds("EPSG:4326", src.crs, *box_bounds(site["lat"], site["lon"]))
                win = from_bounds(*b, transform=src.transform)
                arr = src.read(1, window=win)
            v = arr[arr >= 0]
            out[col] = round(float(v.mean()) / 10, 1) if v.size else np.nan  # g/kg or cm3/dm3 -> %
    return out


def main():
    # Optional: argv[2] = comma-separated site indices, argv[3] = output file
    # (lets the pool run in parallel chunks that are merged afterwards).
    sites = SITES
    out_name = "earth_profiles.csv"
    if len(sys.argv) > 2 and sys.argv[2]:
        sites = [SITES[int(i)] for i in sys.argv[2].split(",")]
    if len(sys.argv) > 3 and sys.argv[3]:
        out_name = sys.argv[3]
    rows = []
    for site in sites:
        row = {k: site[k] for k in ["site_name", "country", "lat", "lon", "site_type",
                                    "terrain_type", "analog_note"]}
        print("site:", site["site_name"], flush=True)
        for fn, label in [(terrain_stats, "terrain"), (power_temperature, "temperature"), (soilgrids, "soil")]:
            try:
                row.update(fn(site))
            except Exception as e:
                print(f"  {label} FAILED: {type(e).__name__} {str(e)[:200]}")
        row["sources"] = ("Copernicus DEM GLO-30 (ESA), NASA POWER climatology, SoilGrids 2.0 (ISRIC)")
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, out_name), index=False)
    print(df.to_string())
    print("Wrote outputs/" + out_name)


if __name__ == "__main__":
    main()

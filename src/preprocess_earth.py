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

SITES = [
    {"site_name": "Atacama Desert", "country": "Chile", "lat": -23.86, "lon": -69.13,
     "site_type": "Hyper-arid high-altitude desert", "tile": "S24_00_W070_00"},
    {"site_name": "McMurdo Dry Valleys", "country": "Antarctica", "lat": -77.47, "lon": 162.52,
     "site_type": "Polar desert / permafrost", "tile": "S78_00_E162_00"},
    {"site_name": "Haughton Crater, Devon Island", "country": "Canada", "lat": 75.38, "lon": -89.68,
     "site_type": "Polar impact crater", "tile": "N75_00_W090_00"},
    {"site_name": "Iceland Volcanic Fields", "country": "Iceland", "lat": 64.90, "lon": -19.10,
     "site_type": "Volcanic highland desert", "tile": "N64_00_W020_00"},
    {"site_name": "Meteor Crater", "country": "USA (Arizona)", "lat": 35.03, "lon": -111.02,
     "site_type": "Impact crater", "tile": "N35_00_W112_00"},
    {"site_name": "Rio Tinto", "country": "Spain", "lat": 37.72, "lon": -6.92,
     "site_type": "Acidic volcanic / Mars analog terrain", "tile": "N37_00_W007_00"},
    {"site_name": "Mauna Kea Volcanic Field", "country": "USA (Hawaii)", "lat": 19.82, "lon": -155.47,
     "site_type": "Basaltic volcanic field", "tile": "N19_00_W156_00"},
    {"site_name": "Svalbard (Adventdalen)", "country": "Norway", "lat": 78.22, "lon": 15.63,
     "site_type": "High-Arctic polar desert", "tile": "N78_00_E015_00"},
]


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
    rows = []
    for site in SITES:
        row = {k: site[k] for k in ["site_name", "country", "lat", "lon", "site_type"]}
        print("site:", site["site_name"], flush=True)
        for fn, label in [(terrain_stats, "terrain"), (power_temperature, "temperature"), (soilgrids, "soil")]:
            try:
                row.update(fn(site))
            except Exception as e:
                print(f"  {label} FAILED: {type(e).__name__} {str(e)[:200]}")
        row["sources"] = ("Copernicus DEM GLO-30 (ESA), NASA POWER climatology, SoilGrids 2.0 (ISRIC)")
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "earth_profiles.csv"), index=False)
    print(df.to_string())
    print("Wrote outputs/earth_profiles.csv")


if __name__ == "__main__":
    main()

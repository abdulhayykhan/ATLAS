"""ATLAS — Mars quick-look (the challenge title includes Mars).

Reads ONE window of the NASA MGS MOLA MEGDR topography tile megt44n000hb
(128 px/deg, simple cylindrical, NASA PDS) via HTTP range requests — the full
tile is 130 MB; the Jezero window is ~3 MB — and computes the same terrain
statistics used for the Moon and Earth, for Jezero Crater (18.44 N, 77.45 E),
the Perseverance rover landing site.

Writes outputs/mars_profiles.csv.
"""
import os
import subprocess

import numpy as np
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
os.makedirs(OUT, exist_ok=True)
URL = ("https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/"
       "mgsl_300x/meg128/megt44n000hb.img")
PPD = 128              # pixels per degree
ROW_BYTES = 11520 * 2  # LINE_SAMPLES * 2 bytes
MARS_DEG_KM = 59.27    # km per degree at the equator (R = 3390 km)


def fetch_window(lat_c, lon_c, half_deg=0.18):
    r0 = int((44.0 - (lat_c + half_deg)) * PPD)
    nrows = int(2 * half_deg * PPD)
    start = r0 * ROW_BYTES
    length = nrows * ROW_BYTES
    raw = subprocess.run(
        ["curl", "-sL", "-r", f"{start}-{start + length - 1}", URL],
        capture_output=True, check=True).stdout
    grid = np.frombuffer(raw, dtype=">i2").reshape(nrows, 11520)
    c0 = int(lon_c * PPD - half_deg * PPD)
    return grid[:, c0:c0 + int(2 * half_deg * PPD)].astype(np.float32)


def main():
    lat, lon = 18.44, 77.45  # Jezero Crater
    z = fetch_window(lat, lon)
    px_m = MARS_DEG_KM * 1000 / PPD
    # dx shrinks by cos(lat); dy does not
    gy, gx = np.gradient(z, px_m, px_m * np.cos(np.radians(lat)))
    slope = np.degrees(np.arctan(np.sqrt(gx ** 2 + gy ** 2)))
    row = {
        "mars_region": "Jezero Crater", "lat": lat, "lon": lon,
        "elev_mean_m": round(float(z.mean()), 1),
        "elev_std_m": round(float(z.std()), 1),
        "slope_mean_deg": round(float(slope.mean()), 2),
        "pct_slope_under_5deg": round(100 * float(np.mean(slope < 5)), 1),
        "pct_slope_under_10deg": round(100 * float(np.mean(slope < 10)), 1),
        "source": "NASA MGS MOLA MEGDR megt44n000hb (PDS), 128 px/deg window via HTTP range",
    }
    df = pd.DataFrame([row])
    df.to_csv(os.path.join(OUT, "mars_profiles.csv"), index=False)
    print(df.to_string())
    print("Wrote outputs/mars_profiles.csv")


if __name__ == "__main__":
    main()

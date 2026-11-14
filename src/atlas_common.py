"""ATLAS shared utilities: PDS3 label parsing + polar-stereographic ROI extraction.

The rasterio/GDAL wheel in many environments ships without the PDS driver, so
LOLA/Diviner IMG products are read directly: the detached PDS3 label (.lbl)
gives LINES, LINE_SAMPLES, SAMPLE_BITS, SCALING_FACTOR, OFFSET and the
polar-stereographic map-projection offsets, and the .img is a raw binary grid.

Orientation convention (validated empirically against named craters —
south: Amundsen, Shoemaker, Faustini, Haworth, Sverdrup, de Gerlache on
LDEM_80S_80M; north: Rozhdestvenskiy + satellites, Byrd, Sylvester, Peary
on LDEM_80N_80M, scored by crater-floor depression):
    x = rho * sin(lon),  y = -rho * cos(lon)     [metres, lon0 = 0]
    col = SAMPLE_PROJECTION_OFFSET + x / MAP_SCALE
    row = LINE_PROJECTION_OFFSET + y / MAP_SCALE   (SOUTH pole files)
    row = LINE_PROJECTION_OFFSET - y / MAP_SCALE   (NORTH pole files — the
          north GDR grids are stored with the opposite row handedness)
with rho = 2R * tan(pi/4 - |lat|/2 in rad) (spherical polar stereographic,
true scale at the pole, R = 1737.4 km).
"""
import math
import re

import numpy as np

MOON_R_KM = 1737.4

# The four NASA challenge base locations (planetocentric).
BASES = [
    {"base_name": "Peary", "pole": "N", "lat": 88.63, "lon": 24.4, "roi_km": 40, "crater_diam_km": 79},
    {"base_name": "Shackleton", "pole": "S", "lat": -89.67, "lon": 129.78, "roi_km": 15, "crater_diam_km": 21},
    {"base_name": "de Gerlache", "pole": "S", "lat": -88.5, "lon": -87.1, "roi_km": 20, "crater_diam_km": 32},
    {"base_name": "Amundsen", "pole": "S", "lat": -84.5, "lon": 82.8, "roi_km": 60, "crater_diam_km": 103},
]


def parse_lbl(path):
    """Extract the numeric fields needed from a PDS3 detached label."""
    txt = open(path, errors="ignore").read()

    def get(key, cast=float):
        m = re.search(rf"^\s*{key}\s*=\s*([-\d\.]+)", txt, re.M)
        return cast(m.group(1)) if m else None

    return {
        "lines": int(get("LINES")),
        "samples": int(get("LINE_SAMPLES")),
        "sample_bits": int(get("SAMPLE_BITS") or 16),
        "scaling": get("SCALING_FACTOR"),
        "offset": get("OFFSET"),
        "scale_m": get("MAP_SCALE"),
        "line_off": get("LINE_PROJECTION_OFFSET"),
        "sample_off": get("SAMPLE_PROJECTION_OFFSET"),
    }


def open_img(img_path, lbl_path):
    """Return (memmap of raw DN, label dict). Values = DN * scaling + offset,
    except LDEM whose label OFFSET field carries the reference radius in
    metres; its own header comment states HEIGHT = DN * SCALING_FACTOR."""
    lbl = parse_lbl(lbl_path)
    dtype = "<i2" if lbl["sample_bits"] == 16 else "u1"
    arr = np.memmap(img_path, dtype=dtype, mode="r", shape=(lbl["lines"], lbl["samples"]))
    offset = lbl["offset"] or 0.0
    if "LDEM" in img_path.upper():
        offset = 0.0
    return arr, lbl, (lbl["scaling"] or 1.0), offset


def latlon_to_pixel(lbl, lat, lon):
    """Polar-stereographic (spherical, true at pole) lat/lon -> fractional pixel."""
    lat_r = math.radians(lat)
    rho = 2 * MOON_R_KM * 1000 * math.tan(math.pi / 4 - abs(lat_r) / 2)
    lam = math.radians(lon)
    x = rho * math.sin(lam)
    y = -rho * math.cos(lam)
    col = lbl["sample_off"] + x / lbl["scale_m"]
    # North-pole GDR grids are stored with the opposite row handedness
    # (validated by crater-depression test, see module docstring).
    row = lbl["line_off"] + (y if lat < 0 else -y) / lbl["scale_m"]
    return row, col


def roi_values(img_path, lbl_path, lat, lon, roi_km, valid_raw=None, exclude_raw=()):
    """Scaled float values inside a circular ROI around lat/lon.

    valid_raw: optional (min, max) raw-DN range; DN outside it is treated as
    fill/no-data and dropped. exclude_raw: individual DN values to drop —
    needed for LDSM, whose DN = 0 is a no-data marker (verified: pixels with
    DN 0 have ordinary ~10 deg DEM-gradient slopes, not 45 deg; DN 0 spikes
    at ~29% of the polar cap while DN > 0 is only ~0.001%).
    """
    arr, lbl, scaling, offset = open_img(img_path, lbl_path)
    crow, ccol = latlon_to_pixel(lbl, lat, lon)
    r_px = roi_km * 1000 / lbl["scale_m"]
    r0 = max(0, int(crow - r_px - 1)); r1 = min(lbl["lines"], int(crow + r_px + 2))
    c0 = max(0, int(ccol - r_px - 1)); c1 = min(lbl["samples"], int(ccol + r_px + 2))
    sub = np.asarray(arr[r0:r1, c0:c1], dtype=np.float64)
    yy, xx = np.mgrid[r0:r1, c0:c1]
    dist_px = np.sqrt((xx - ccol) ** 2 + (yy - crow) ** 2)
    mask = dist_px <= r_px
    if valid_raw is not None:
        mask &= (sub >= valid_raw[0]) & (sub <= valid_raw[1])
    for bad in exclude_raw:
        mask &= sub != bad
    vals = sub[mask] * scaling + offset
    return vals


def stats(vals):
    if vals is None or len(vals) == 0:
        return {}
    return {
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
        "std": float(np.std(vals)),
        "p10": float(np.percentile(vals, 10)),
        "p90": float(np.percentile(vals, 90)),
        "min": float(np.min(vals)),
        "max": float(np.max(vals)),
        "n": int(len(vals)),
    }
